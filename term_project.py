#!/usr/bin/env python
# coding: utf-8

# In[81]:


import simpy
import random
import pandas as pd

# Constants
RANDOM_SEED = 42
NEW_PATIENTS = 5  # Total number of patients for the simulation
INTERVAL_PATIENTS = 10.0  # Generate new patients roughly every 10 minutes
SIM_TIME = 360  # Simulation time in minutes
TREATMENT_TIME = 15  # Average time a patient spends with the doctor
LAB_TEST_TIME = 10  # Average time for conducting lab tests
RESULTS_WAIT_TIME = 20  # Time to wait for lab results
FOLLOW_UP_TIME = 5  # Time for follow-up consultation

NUM_DOCTORS = 1  # Number of available doctors
NUM_NURSES = 1  # Number of available nurses
NUM_LAB_TECHS = 1  # Number of available lab technicians
NUM_EXAM_ROOMS = 1  # Number of available exam rooms

# Initialize a list to store patient records
patient_records = []

class EmergencyDepartment:
    def __init__(self, env, num_doctors, num_nurses, num_lab_techs, num_exam_rooms):
        self.env = env
        self.doctor = simpy.Resource(env, num_doctors)
        self.nurse = simpy.Resource(env, num_nurses)
        self.lab = simpy.Resource(env, num_lab_techs)
        self.exam_room = simpy.Resource(env, num_exam_rooms)

    def triage(self, patient):
        yield self.env.timeout(random.randint(1, 3))  # Triage takes 1-3 minutes

    def treatment(self, patient):
        yield self.env.timeout(random.randint(5, TREATMENT_TIME))  # Treatment time

    def lab_test(self, patient):
        yield self.env.timeout(random.randint(5, LAB_TEST_TIME))  # Lab test time

    def follow_up(self, patient):
        yield self.env.timeout(FOLLOW_UP_TIME)  # Follow-up consultation time

def patient(env, name, ed):
    arrival_time = env.now
    print(f'{name} arrives at the emergency department at {env.now:.1f}')
    with ed.nurse.request() as request:
        yield request
        triage_start_time = env.now
        yield env.process(ed.triage(name))
        triage_end_time = env.now
        # Nurse decision to admit directly with 5% chance
        if random.random() < 0.05:
            print(f'{name} is directly admitted to the hospital after triage at {env.now:.1f}')
            patient_records.append({
                'Patient': name,
                'Arrival Time': arrival_time,
                'Triage Start': triage_start_time,
                'Triage End': triage_end_time,
                'Outcome': 'Admitted by Nurse'
            })
            return  # Ends the process for this patient as they are admitted
        print(f'{name} leaves triage at {env.now:.1f}')

    with ed.exam_room.request() as request:
        yield request
        with ed.doctor.request() as doc_request:
            yield doc_request
            treatment_start_time = env.now
            yield env.process(ed.treatment(name))
            treatment_end_time = env.now
            print(f'{name} needs lab tests at {env.now:.1f}')

    with ed.lab.request() as lab_request:
        yield lab_request
        lab_start_time = env.now
        yield env.process(ed.lab_test(name))
        lab_end_time = env.now
        print(f'{name} lab test completed at {env.now:.1f}')
    
    # Wait for results
    results_ready_time = env.now + RESULTS_WAIT_TIME
    yield env.timeout(RESULTS_WAIT_TIME)
    print(f'{name} lab results are ready at {env.now:.1f}')

    with ed.doctor.request() as doc_request:
        yield doc_request
        follow_up_start_time = env.now
        yield env.process(ed.follow_up(name))
        follow_up_end_time = env.now
        # Decision making for discharge or admission
        if random.random() < 0.7:  # 70% chance to discharge, 30% to admit
            outcome = 'Discharged'
        else:
            outcome = 'Admitted'
        print(f'{name} {outcome} at {env.now:.1f}')
        patient_records.append({
            'Patient': name,
            'Arrival Time': arrival_time,
            'Triage Start': triage_start_time,
            'Triage End': triage_end_time,
            'Treatment Start': treatment_start_time,
            'Treatment End': treatment_end_time,
            'Lab Test Start': lab_start_time,
            'Lab Test End': lab_end_time,
            'Results Ready': results_ready_time,
            'Follow Up Start': follow_up_start_time,
            'Follow Up End': follow_up_end_time,
            'Outcome': outcome
        })

def setup(env, num_doctors, num_nurses, num_lab_techs, num_exam_rooms):
    emergency_department = EmergencyDepartment(env, num_doctors, num_nurses, num_lab_techs, num_exam_rooms)

    for i in range(NEW_PATIENTS):
        env.process(patient(env, f'Patient {i}', emergency_department))

    while True:
        yield env.timeout(random.expovariate(1.0 / INTERVAL_PATIENTS))
        i += 1
        env.process(patient(env, f'Patient {i}', emergency_department))

# Setup and start the simulation
print('Emergency Department Simulation')
random.seed(RANDOM_SEED)
env = simpy.Environment()
env.process(setup(env, num_doctors=NUM_DOCTORS, num_nurses=NUM_NURSES, num_lab_techs=NUM_LAB_TECHS, num_exam_rooms=NUM_EXAM_ROOMS))
env.run(until=SIM_TIME)

# Convert the list of patient records into a DataFrame
df_patients = pd.DataFrame(patient_records)


# In[82]:


df_patients


# In[83]:


print("Number of Patient Records:", len(df_patients))


# In[84]:


df_discharged = df_patients[df_patients['Outcome'] == 'Discharged']
df_discharged = df_discharged.reset_index()
df_discharged['Total Time'] = df_discharged['Follow Up End'] - df_discharged['Arrival Time']
print("Number of Patients Discharged", len(df_discharged))
print("Average Time in Emergency Department for Discharged Patients:", df_discharged['Total Time'].mean())


# In[85]:


df_admitted = df_patients[df_patients['Outcome'] == 'Admitted']
df_admitted = df_admitted.reset_index()
df_admitted['Total Time'] = df_admitted['Follow Up End'] - df_admitted['Arrival Time']
print("Number of Patients Admitted", len(df_admitted))
print("Average Time in Emergency Department for Admitted Patients:", df_admitted['Total Time'].mean())


# In[ ]:




