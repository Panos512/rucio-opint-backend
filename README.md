# rucio-opint-backend
Be aware that this project is still in its early phase.

## Description
the backend of rucio's operational intelligence is composed using the flask microframework and SQLite for the relational database.
The backend is responsible for delivering an API to the frontend which can be used to create, read, and update any of the tables in the database except "Error_category".

The backend contains a errorpopulation script which is supposed to be run every hour by a cron job, this script will cover and detect errors that are causing transfer/deletion inefficiencies. these errors are then supposed to be read by operators/shifters who have the option to take an action, a suggested action will be provided (actions are also read using the API) and if an action is taken, they then have the option to provide feedback,
on whether or not the action resulted in success. Their feedback will be saved in the database and used for creating better action suggestions in the future.

## Setup:
- Have python3 and pip installed

- Fork the repository
- Clone it to your local system

```
git clone https://github.com/DilaksunB/rucio-opint-backend
```
- Enter the repository
```
cd rucio-opint-backend
```
- Create a virtual environment
```
python -m virtualenv venv
```
- Enter the virtual environment
```
source venv/bin/activate
```
- Install the requirements into your virtual environment from the requirements.txt
```
pip install -r requirements.txt
```
The virtual environment is now set, and you should be able to launch the web server with:
```
python OI_flask_API.py
```
