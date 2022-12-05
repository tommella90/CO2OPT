### EXPOLORE DATA
import pandas as pd
import numpy as np
import geopy.distance
from sklearn.cluster import KMeans


#%%
df = pd.read_csv('warehouse_short.txt', sep=",")

#%% things to make 'offline'

# create a list of all vehicles labels
vehicles = list(df['vehicle_id'].unique())

# clusterize vehicles based on driving condition
# for now: assign random values to each column
driving_conditions = pd.DataFrame(np.random.randint(0,10,(len(df['vehicle_id'].unique()), 5)))


## Calculate the predicted label per each veichle
kmeans = KMeans(n_clusters=4, random_state=1234)
kmeans.fit(driving_conditions)
driving_conditions["cluster"] = kmeans.predict(driving_conditions)
driving_conditions['vehicle_id'] = df['vehicle_id'].unique()

df = df.merge(driving_conditions, right_on="vehicle_id", left_on="vehicle_id")

# store driving fixed information per each vehicle (more to add)
driving_info = df[['avg_fuel_consumption', 'engine_speed', 'ignition_time', 'surface_type']]

#%%

# Calculate distance per each vehicle in the time-frame available
def calculate_fuel_per_km(veichle_id):
    ## group by veichle
    vehicle = df.loc[df['vehicle_id']==veichle_id]
    vehicle = vehicle.reset_index()

    # Calculate distance per each veichle in the time-frame available
    distances = []
    for position in range(1, len(vehicle.index)-1):
        lat1, lon1 = vehicle.loc[position, "longitude"], vehicle.loc[position, "longitude"]
        lat2, lon2 = vehicle.loc[position-1, "longitude"], vehicle.loc[position-1, "longitude"]
        distances.append(geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).km)
    km_travelled = sum(distances)

    # calculate fuel used
    fuel_used = vehicle['total_fuel_used'][len(vehicle.index)-1] - vehicle['total_fuel_used'][0]
    fuel_per_km = fuel_used * 1 / km_travelled        # relate to 1 km

    return km_travelled, fuel_per_km


# Comparison to other vehicles observed with similar driving conditions
# get one veichle id as an example --> get its assigned cluster

def register_time_stamp(veichle_id):
    ## group by veichle
    return list(df.loc[df['vehicle_id']=='x1sdt0ier']['unix_timestamp'])[-1]


# Create a usage profile per vehicle:
# as an example, I create three groups based on fuel used / km: low, mid and high consumers
# (Ideally, I would clusterize based on more technical categories)
# For now, I'll use 3 arbitraty tresholds
def usage_profile_per_vehicle(veichle_id):
    fuel_consumption = calculate_fuel_per_km(veichle_id)[1]
    if fuel_consumption < 40:
        vehicle_profile = "Low user"
    elif fuel_consumption >= 40 and fuel_consumption < 100:
        vehicle_profile = "Mid user"
    else:
        vehicle_profile = "High user"

    return vehicle_profile



#%% Let's say that I want to show performances from the first id_vehicle: "x1sdt0ier"
# Every 2 minutes, I'll add the following json structure

def extract_vehicle_instant_info(vehicle_id):
    # get the info relative to a single vehicle for a single data entry
    dict_info = {
        "vehicle_id": vehicle_id,
        "fuel_consumption_per_km": calculate_fuel_per_km(vehicle_id)[1],
        "km_travelled": calculate_fuel_per_km(vehicle_id)[0],
        "vehicle_profile": usage_profile_per_vehicle(vehicle_id),
        "vehicle_group": list(df.loc[df['vehicle_id']==vehicle_id]['cluster'])[0],
        "time_stamp": register_time_stamp(vehicle_id)
    }
    return dict_info


def extract_all_vehicles_info(vehicle_list):
    vehicles_info = []
    for vehicle_id in vehicle_list:
        vehicles_info.append(extract_vehicle_instant_info(vehicle_id))

    return vehicles_info


def compare_similar_vehicles(vehicle_id):
    list_vehicles =  list(df['vehicle_id'].unique())
    vehicles = pd.DataFrame(extract_all_vehicles_info(list_vehicles))
    group = vehicles.loc[vehicles['vehicle_id']==vehicle_id, "vehicle_group"][0]
    return vehicles.loc[vehicles['vehicle_group']==group]



#%% HYPOTHESIS on how to proceed: I update a higher level file which contains all the information arriving every minute:
# At the end of the day I'll sum up the following performances:

def main():

    ## MAIN function
    daily_info = pd.DataFrame(extract_all_vehicles_info(vehicles))

    choice = input("""
    -(A)Show all the vehicles\n 
    -(S)ingle vehicle\n 
    -(G)Show similar vehicles\n"
    """)

    # 1) Display all daily vehicles info
    if choice == "A":
        return daily_info

    # 2) Display a single vehicle info (choose vehicle by id)
    elif choice == "S":
        choose_vehicle = input("\n      Choose a vehicle id\n")
        daily_info_single_vehicle = daily_info.loc[daily_info['vehicle_id']==choose_vehicle]
        return daily_info_single_vehicle

    # 3) Display a vehicle and all its similar veichles (choose vehicle by id)
    elif choice == "G":
        choose_vehicle = input("\n      Choose a vehicle id\n")
        similar_vehicles = compare_similar_vehicles(choose_vehicle)
        return similar_vehicles


#%%

main()

## example veichle_id:
## x1sdt0ier


#%% I create random values for demonstrational purposes (with 100 observations)
df = pd.DataFrame(extract_all_vehicles_info(vehicles))

"""
TO COMPLETE: 
    Identify the number of trips:
    For this task I'd use the daily report and use teh variable "is_moving" to check 
    the lengh of the stop. After a certain treshold it could be considered a new trip. 
    After splitting the trips, I'd check the most economic one in terms of C02 
    (simple comparison)
    The main() function would work on the new dataframe just created (after appending
    over time all the new observations)
"""




#%%
