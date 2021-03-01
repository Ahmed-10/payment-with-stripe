from flask import Flask, render_template, request, redirect, jsonify
from .db import User, db, Plans
from .subscription import create_customer, get_customer_plan, force_subscription, update
from .stripe_config import set_environ
import threading
import os

set_environ()

# INTEGRATION NOTE #6: a seperate thread that update and charge user for subscription periodically 
sec_thread = threading.Thread(target=update)
sec_thread.daemon = True
sec_thread.start()

# database_name = "test"
# postgres_user = "postgres"
# password = "root"

# database_uri = "postgresql://{}:{}@{}/{}".format(
#     postgres_user,
#     password,
#     'localhost:5432',
#     database_name
#     )

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
# db.create_all()


@app.route('/')
def index():
    _users = User.query.all()
    users = [user.format() for user in _users]
    return render_template('signup.html', users=users)


@app.route("/sign-up", methods=["POST"])
def sign_up():
    company = request.form.get("company")
    email = request.form.get("email")

    user = User(email, company)
    try:
        user.insert()

        # INTEGRATION NOTE #6: create a new customer 
        # ---------------- start ----------------
        """
        create_customer:
        arguemeents: dict {
            'id': user primary key (should be unique),
            'email' user email (should be unique),
            'company': user company name
        }
        return: 
            - when everything is ok => dict {
                'message': 'success'
            }
            - when something goes wrong => dict {
                'message': error message
            }
        """
        response = create_customer(user.format())
        # ---------------- end ----------------

        if(response['message'] == 'success'):
            return redirect('profile/' + str(user.id))
        else:
            user.delete()
            return response

    except Exception as error:
        user.rollback()
        return str(error)



@app.route('/profile/<id>')
def profile(id):
    try:
        _user = User.query.get(int(id))

        # INTEGRATION NOTE #6: check customer pricing plan
        # ---------------- start ----------------
        """
            get_customer_plan:
            arguemeents: integer
                'id': user primary key
            return: 
                - when everything is ok => dict {
                    'plan': customer plan as string
                }
                - when something goes wrong => dict {
                    'message': error message
                }
        """
        response = get_customer_plan(_user.id)
        # ---------------- end ----------------

        if 'plan' in response:
            user = _user.format()
            user['plan'] = response['plan']

            _plans = Plans.query.all()
            plans = [plan.format() for plan in _plans]
            return render_template('profile.html', user=user, plans=plans)
        else:
            return response

    except Exception as error:
        return str(error)


@app.route('/force-subscription/<id>', methods=['POST'])
def method_name(id):
    plan = request.form.get('new-plan')
    response = force_subscription(id, plan)
    if response['message'] == 'success':
        return redirect('/profile/' + id)
    else:
        return jsonify(response)


# INTEGRATION NOTE #0: add subscription views
from flaskr import subscription_views

if __name__ == '__main__':
  app.run()
 