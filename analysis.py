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


class FuelCalculator:
    def __init__(self, dataframe):
        self.df = dataframe

    def calculate_fuel_per_km(self, veichle_id):

        ## group by veichle
        vehicle = self.df.loc[self.df['vehicle_id']==veichle_id]
        vehicle = vehicle.reset_index()

        # Calculate distance per each veichle in the time-frame available
        distances = []
        for position in range(1, len(vehicle.index)-1):
            lat1, lon1 = vehicle.loc[position, "longitude"], vehicle.loc[position, "latitude"]
            lat2, lon2 = vehicle.loc[position-1, "longitude"], vehicle.loc[position-1, "latitude"]
            distances.append(geopy.distance.geodesic((lat1, lon1), (lat2, lon2)).km)
        km_travelled = sum(distances)

        # calculate fuel used
        fuel_used = vehicle['total_fuel_used'][len(vehicle.index)-1] - vehicle['total_fuel_used'][0]
        fuel_per_km = fuel_used * 1 / km_travelled        # relate to 1 km

        return km_travelled, fuel_per_km


    def register_time_stamp(self, veichle_id):
        return list(df.loc[df['vehicle_id']==veichle_id]['unix_timestamp'])[-1]


    def usage_profile_per_vehicle(self, veichle_id):
        fuel_consumption = self.calculate_fuel_per_km(veichle_id)[1]
        if fuel_consumption < 40:
            vehicle_profile = "Low user"
        elif fuel_consumption >= 40 and fuel_consumption < 100:
            vehicle_profile = "Mid user"
        else:
            vehicle_profile = "High user"

        return vehicle_profile


    def extract_vehicle_instant_info(self, vehicle_id):
        # get the info relative to a single vehicle for a single data entry
        dict_info = {
            "vehicle_id": vehicle_id,
            "fuel_consumption_per_km": self.calculate_fuel_per_km(vehicle_id)[1],
            "km_travelled": self.calculate_fuel_per_km(vehicle_id)[0],
            "vehicle_profile": self.usage_profile_per_vehicle(vehicle_id),
            "vehicle_group": list(df.loc[df['vehicle_id']==vehicle_id]['cluster'])[0],
            "time_stamp": self.register_time_stamp(vehicle_id)
        }
        return dict_info


    def extract_all_vehicles_info(self, vehicle_list):
        vehicles_info = []
        for vehicle_id in vehicle_list:
            vehicles_info.append(self.extract_vehicle_instant_info(vehicle_id))

        return vehicles_info


    def compare_similar_vehicles(self, vehicle_id):
        list_vehicles =  list(df['vehicle_id'].unique())
        vehicles = pd.DataFrame(self.extract_all_vehicles_info(list_vehicles))
        group = vehicles.loc[vehicles['vehicle_id']==vehicle_id, "vehicle_group"][0]
        return vehicles.loc[vehicles['vehicle_group']==group]


calculator = FuelCalculator(df)

#%% CALCULATE FUEL BY VEHICLE
km_travelled, fuel_per_km = calculator.calculate_fuel_per_km("x1sdt0ier")

#%% CALCULATE USAGE PROFILE BY VEHICLE
calculator.usage_profile_per_vehicle("x1sdt0ier")

#%% EXTRACT SINGLE VEHICLE INFO
calculator.extract_vehicle_instant_info("x1sdt0ier")

#%% COMPARE THE VEHICLE INFO WITH VEHICLES FROM THE SAME GROUP
calculator.compare_similar_vehicles("x1sdt0ier")

#%% FIND ALL VEHICLES INFORMATION
info = pd.DataFrame(calculator.extract_all_vehicles_info(vehicles))
info
#%%
df.columns
#%%
