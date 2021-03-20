import os
import psycopg2


# Program parameter
camera_angle = 90
is_write_to_the_database = True

is_display_tracking = True
fig_ylim = [0.0, 10.0]
fig_xlim = [-3, 3]
display_tracking_width = 480
display_tracking_height = 270

# Database connect
if is_write_to_the_database:
    DB_NAME = os.environ['DB_NAME']
    DB_USER = os.environ['DB_USER']
    DB_HOST = os.environ['SMART_SPACE_TRACKING_POSTGRES_PORT_5432_TCP_ADDR']
    DB_PASSWORD = os.environ['DB_PASSWORD']
    DB_PORT = os.environ['DB_PORT']
    database_connect = psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST, password=DB_PASSWORD, port=DB_PORT)
