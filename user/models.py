from flask import Flask, jsonify, request, session, redirect, flash
from discord_webhook import DiscordWebhook, DiscordEmbed
from passlib.hash import pbkdf2_sha256
from app import db
import uuid
import configparser
config = configparser.ConfigParser()
config.read('config.ini')


class User:

    def start_session(self, user):
        """
        Function to start a new session when user is loggin in
        :param user: user object
        :return: user object with code 200 (successful session creation)
        """
        del user['password']
        session['logged_in'] = True
        session['user'] = user
        return jsonify(user), 200

    def signup(self):
        """
        function to create a new user.
        Encrypt Password using hash function.

        """
        # Create the user object
        user = {
            "_id": uuid.uuid4().hex,
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password'),
            "role": 'app_user'
        }

        # Encrypt the password
        user['password'] = pbkdf2_sha256.encrypt(user['password'])

        # Check for existing email address
        if db.users.find_one({"email": user['email']}):
            return jsonify({"error": "Email address already in use"}), 400

        if db.users.insert_one(user):
            return self.start_session(user)

        return jsonify({"error": "Signup failed"}), 400

    def signout(self):
        """
        Function to Signout and clear the session
        :return: redirect the user to home page.
        """
        session.clear()
        return redirect('/')

    def login(self):
        """
        Function to login
        :return: new session with user details
        """
        user = db.users.find_one({
            "email": request.form.get('email')
        })

        # Check if user email exist and password in the form and encrypted password from db are same
        if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
            return self.start_session(user)

        return jsonify({"error": "Invalid login credentials"}), 401

    def update_password(self):
        print(request.form)

        # Check for existing email address

        # Create the user object
        user_update = {
            "email": request.form.get('email'),
            "password": request.form.get('password'),
            "confirm_password": request.form.get('confirmpassword')
        }

        if not db.users.find_one({"email": user_update['email']}):
            return jsonify({"error": "Email Id doesn't Exist"}), 400

        user = db.users.find_one({"email": user_update['email']})

        # Check password and confirm password should be same:
        if user_update['password'] != user_update['confirm_password']:
            return jsonify({"error": "Password doesn't match"}), 400

        # Check if user email exist and password in the form and encrypted password from db are same
        if user and pbkdf2_sha256.verify(user_update['password'], user['password']):
            return jsonify({"error": "New password must be different"}), 400

        # Encrypt the password
        user_update['password'] = pbkdf2_sha256.encrypt(user_update['password'])
        user_update['confirm_password'] = pbkdf2_sha256.encrypt(user_update['confirm_password'])

        users = db.users
        users.find_one_and_update(
            {'email': user_update['email']},
            {'$set':
                 {'password': user_update['password']}
             }, upsert=False
        )

        return jsonify(user), 200


    def sendtodiscord(self):
        webhook = DiscordWebhook(url=config.get('main', 'webhook'), content='Your Text Summary is Ready...')
        webhook.add_file(file=request.form.get('message'), filename='summary.txt')
        if webhook.execute():
            return jsonify({"success": "Message sent successfully"}), 200
        else:
            return jsonify({"error": "Message failed"}), 400


    # -------------------------- User Management ----------------------- #

    def createuser(self):
        """
        function to create a new user by Admin.
        Encrypt Password using hash function.

        """
        # Create the user object
        user = {
            "_id": uuid.uuid4().hex,
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password'),
            "role": request.form.get('role')
        }

        # Encrypt the password
        user['password'] = pbkdf2_sha256.encrypt(user['password'])

        # Check for existing email address
        if db.users.find_one({"email": user['email']}):
            return jsonify({"error": "Email address already in use"}), 400

        if db.users.insert_one(user):
            flash("User Created Successfully!")
            return jsonify({"success": "User Created Successfully"}), 200

        return jsonify({"error": "Signup failed"}), 400

    def deleteuser(self):

        # Check for existing email address and delete user

        # Create the user object
        user_email = request.form.get('email')

        if not db.users.find_one({"email": user_email}):
            return jsonify({"error": "Email Id doesn't Exist"}), 400

        user = db.users.find_one({"email": user_email})

        if user:
            users = db.users
            users.delete_one(user)

        return jsonify({"success": "User deleted successfully!"}), 200

    def updateuser(self):

        # Check for existing email address and update user

        # Update the user object
        user_email = request.form.get('email')
        user_new_name = request.form.get('name')
        user_new_role = request.form.get('role')

        if not db.users.find_one({"email": user_email}):
            return jsonify({"error": "Email Id doesn't Exist"}), 400

        user = db.users.find_one({"email": user_email})

        if user:
            if user_new_name == user['name'] and user_new_role == user['role']:
                return jsonify({"error": "Entered values are same as before. Please update"}), 400
            users = db.users
            users.find_one_and_update(
                {'email': user_email},
                {'$set':
                     {'name': user_new_name, 'role': user_new_role},
                 }, upsert=False
            )


        return jsonify({"success": "User updated successfully!"}), 200


    def getusers(self):
        """
        Function to get user details from DB
        :return: JSON with user details
        """
        users_data = []
        for each_user in db.users.find():
            users_data.append({'Name': each_user['name'],
                               'Email Id': each_user['email']})
        return jsonify(users_data), 200