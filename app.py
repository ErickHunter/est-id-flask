from flask import Flask, render_template, request, jsonify
from ldap3 import Server, Connection, ALL, Tls
import ssl


app = Flask(__name__)

# Global array to store the digits of the Estonian ID code
id_code = [None] * 10


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


def query_ldap_by_id_code(organization, id_code):
    # Define the LDAP server
    server_url = 'ldaps://esteid.ldap.sk.ee:636'

    # Adjust the base DN to include the organization component
    print("org is!!!")
    print(organization)
    base_dn = f"o={organization},dc=ESTEID,c=EE"

    # Construct the search filter using the provided ID code
    query_filter = f"(serialNumber=PNOEE-{id_code})"
    print("ID code is!!!")
    print(id_code)
    # Setup LDAP connection without CA certificate verification
    tls_configuration = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLS_CLIENT)
    server = Server(server_url, use_ssl=True, tls=tls_configuration)

    try:
        # Connect to the server using anonymous bind
        with Connection(server, auto_bind=True) as conn:
            # Perform the search with the provided filter
            conn.search(base_dn, query_filter, attributes=['*'])
            # Process the search results
            if conn.entries:
                for entry in conn.entries:
                    print(entry)
                    # Further processing can be done as needed
            else:
                print("No entries found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def populate_id_code(sex, date_of_birth, serial, control_code):
    year, month, day = map(int, date_of_birth.split('-'))
    first_digit = determine_first_digit(sex, year)
    id_code[0] = first_digit
    id_code[1:3] = date_of_birth[2:4]  # YY from YYYY-MM-DD
    id_code[3:5] = date_of_birth[5:7]  # MM
    id_code[5:7] = date_of_birth[8:10] # DD
    id_code[7:9] = list(serial)
    id_code[10:] = list(control_code)




@app.route('/')
def form():
    return render_template('ldap-form.html')


@app.route('/search', methods=['POST'])
def search():
    if request.form['action'] == 'start_search':
        code_type = request.form['code_type']
        date_of_birth = request.form['date_of_birth']
        sex = request.form['sex']
        serial = request.form['serial']
        control_code = request.form['control_code']

        populate_id_code(sex, date_of_birth, serial, control_code)

        id_code_str = ''.join(str(digit) for digit in id_code)
        id_code_int = int(id_code_str)

        # Perform LDAP search and get the response
        search_results = query_ldap_by_id_code(code_type, id_code_int)
        print(search_results)
        # Return the search results as JSON
        return jsonify(search_results)




if __name__ == '__main__':
    app.run(debug=True)
