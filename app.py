from flask import Flask, render_template, request

app = Flask(__name__)

# Global array to store the digits of the Estonian ID code
id_code = [None] * 11


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


@app.route('/')
def form():
    return render_template('ldap-form.html')


@app.route('/search', methods=['POST'])
def search():
    if request.form['action'] == 'start_search':
        # Extract form data
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        date_of_birth = request.form['date_of_birth']
        sex = request.form['sex']
        serial = request.form['serial']
        control_code = request.form['control_code']

        # Implement LDAP search logic here

        return "Search Started. Implement the actual search logic here."

    elif request.form['action'] == 'stop_search':
        # Implement logic to stop search
        return "Search Stopped. Implement the actual logic to stop search here."

    return "Invalid action."


if __name__ == '__main__':
    app.run(debug=True)
