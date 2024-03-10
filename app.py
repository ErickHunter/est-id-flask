from flask import Flask, render_template, request, jsonify
from ldap3 import Server, Connection, Tls
import ssl


app = Flask(__name__)


# Function to determine the first digit of the Estonian ID code
def determine_first_digit(sex, year):
    if sex == 'male':
        if 1800 <= year <= 1899:
            return '1'
        elif 1900 <= year <= 1999:
            return '3'
        elif 2000 <= year <= 2099:
            return '5'
        elif 2100 <= year <= 2199:
            return '7'
    elif sex == 'female':
        if 1800 <= year <= 1899:
            return '2'
        elif 1900 <= year <= 1999:
            return '4'
        elif 2000 <= year <= 2099:
            return '6'
        elif 2100 <= year <= 2199:
            return '8'
    return None


def calculate_control_code(id_code_digits):
    # Define Level I and Level II weights
    level_1_weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1]
    level_2_weights = [3, 4, 5, 6, 7, 8, 9, 1, 2, 3]

    # Calculate sum of products Level I
    sum_level_1 = sum(id_code_digit * weight for id_code_digit, weight in zip(id_code_digits, level_1_weights))
    remainder_level_1 = sum_level_1 % 11

    if remainder_level_1 < 10:
        return remainder_level_1  # Control number found with Level I weights

    # Calculate sum of products Level II if remainder from Level I is 10
    sum_level_2 = sum(id_code_digit * weight for id_code_digit, weight in zip(id_code_digits, level_2_weights))
    remainder_level_2 = sum_level_2 % 11

    if remainder_level_2 < 10:
        return remainder_level_2  # Control number found with Level II

    # Remainder from Level II is also 10, control number is 0
    return 0


def query_ldap_by_id_code(organization, id_code):
    # LDAP server address
    server_url = 'ldaps://esteid.ldap.sk.ee:636'

    # Base DN organization component
    base_dn = f"o={organization},dc=ESTEID,c=EE"

    # Search filter using provided ID code
    query_filter = f"(serialNumber=PNOEE-{id_code})"

    # Setup LDAP connection without CA certificate verification
    tls_configuration = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
    server = Server(server_url, use_ssl=True, tls=tls_configuration)
    search_results = []  # Initialize an empty list to store search results

    try:
        # Connect to the server, anonymous bind
        with Connection(server, auto_bind=True) as conn:
            conn.search(base_dn, query_filter, attributes=['*'])
            if conn.entries:
                for entry in conn.entries:
                    # Skip the loop iteration if the entry is None
                    if entry is None:
                        continue
                    # Convert each entry to a dictionary and add to the results list
                    cn_value = entry.entry_attributes_as_dict['cn'][0]
                    search_results.append(cn_value)
            else:
                print("No entries found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return search_results


def generate_estonian_id_code(sex, date_of_birth, serial):
    # Determine first digit
    year = int(date_of_birth[:4])
    first_digit = determine_first_digit(sex, year)

    # Populate first 10 digits of ID code
    year_short = date_of_birth[2:4]
    month = date_of_birth[5:7]
    day = date_of_birth[8:10]
    initial_id_code_str = f"{first_digit}{year_short}{month}{day}{serial}"

    # Calculate control code
    initial_id_code_digits = [int(digit) for digit in initial_id_code_str]
    control_code = calculate_control_code(initial_id_code_digits)

    # Form complete ID code
    complete_id_code = f"{initial_id_code_str}{control_code}"

    return complete_id_code


@app.route('/est-id-search')
def home():
    return render_template('ldap-form.html')


@app.route('/search')
def form1():
    return render_template('ldap-form.html')


@app.route('/search-range')
def form2():
    return render_template('ldap-form-range.html')


@app.route('/search', methods=['POST'])
def search():
    if request.form['action'] == 'start_search':
        code_type = request.form['code_type']
        date_of_birth = request.form['date_of_birth']
        sex = request.form['sex']
        serial = request.form['serial']

        print(generate_estonian_id_code(sex, date_of_birth, serial))
        complete_id_code = generate_estonian_id_code(sex, date_of_birth, serial)

        # Start a LDAP search
        search_results = query_ldap_by_id_code(code_type, complete_id_code)
        print(search_results)
        # Flask return search results as JSON
        return jsonify(search_results)


@app.route('/search-range', methods=['POST'])
def search_range():
    if request.form['action'] == 'start_search':
        code_type = request.form['code_type']
        sex = request.form['sex']
        date_of_birth = request.form['date_of_birth']
        serial_start = int(request.form['serial_start'])
        serial_end = int(request.form['serial_end'])

        results = []
        for serial in range(serial_start, serial_end + 1):
            serial_str = f"{serial:03}"  # Format serial number as a zero-padded string
            complete_id_code = generate_estonian_id_code(sex, date_of_birth, serial_str)
            search_results = query_ldap_by_id_code(code_type, complete_id_code)
            if search_results:
                results.extend(search_results)

        # Return the combined search results as JSON
        return jsonify(results)

    return "Invalid form submission", 400


if __name__ == '__main__':
    app.run(debug=True)
