from flask import Flask, render_template, request

app = Flask(__name__)


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
        place_of_birth = request.form['place_of_birth']
        hospital_of_birth = request.form['hospital_of_birth']
        sex = request.form['sex']
        id_code = request.form['id_code']

        # Implement your LDAP search logic here
        # For example, you might use the extracted form data to query an LDAP server

        return "Search Started. Implement the actual search logic here."

    elif request.form['action'] == 'stop_search':
        # Implement logic to stop search if possible
        return "Search Stopped. Implement the actual logic to stop search here."

    return "Invalid action."


if __name__ == '__main__':
    app.run(debug=True)
