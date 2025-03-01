from tkinter import Tk, Label, StringVar, TOP, BOTH
import requests
import psutil as ps
import numpy as np
from datetime import timedelta, datetime, timezone
from win10toast import ToastNotifier
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

toast = ToastNotifier()

battery = ps.sensors_battery()

def fetch_percent():
    return battery.percent

def fetch_charging_status():
    return battery.power_plugged

def get_location():
    response = requests.get('https://ipinfo.io/json')
    data = response.json()
    
    # "IP Address: {data.get('ip')}")
    # "City: {data.get('city')}")
    # "Region: {data.get('region')}")
    # "Country: {data.get('country')}")
    # "Location: {data.get('loc')}")  # Latitude, Longitude
    
    return data

print(fetch_percent())
print(fetch_charging_status())
print(get_location().get('loc'))

#################
# Make API Account details
# Username: GridWise_2025
# Password: grid_wise_medhansh_rishit_buhhs_2025
# Email: rishit.avadhuta@gmail.com
#################
def register():
    register_url = 'https://api.watttime.org/register'
    params = {'username': 'GridWise_2025',
            'password': 'Grid_Wise_medhansh_rishit_buhhs_2025#',
            'email': 'rishit.avadhuta@gmail.com',
            'org': 'GridWise'}
    rsp = requests.post(register_url, json=params)
    print(rsp.text)


def plot_graph(x, y):
    # Create a Matplotlib figure
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(x, y, marker='o', linestyle='-')
    ax.set_title('lbs CO2/MWh over Time')
    ax.set_xlabel('Time (minutes into the future)')
    ax.set_ylabel('lbs CO2')

    # Embed the figure into Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)

def get_energy_mix(username, password, location, tk: Tk, textvar: StringVar):
    lat, lon = map(float, location.split(','))

    auth_response = requests.post(
        "https://api.watttime.org/login", auth=(username, password))

    token = auth_response.json()['token']
    headers = {"Authorization": f"Bearer {token}"}

    region = requests.get("https://api.watttime.org/v3/region-from-loc", headers=headers, params={"latitude": lat, "longitude": lon, "signal_type": "co2_moer"}).json()['region']
    
    if auth_response.status_code != 200:
        return {"error": f"Authentication failed: {auth_response.text}"}
    

    url = "https://api.watttime.org/v3/forecast"
    
    params = {
        "region": "CAISO_NORTH",
        "signal_type": "co2_moer",
        "horizon_hours": 72
    }

    response = requests.get(url, headers=headers, params=params)
    moer_list = []
    for i in range(72 * 12):
        print(response.json()['data'][i]['value'])
        moer_list.append(response.json()['data'][i]['value'])
    print(np.mean(moer_list))
    print(np.std(moer_list))
    green_energy_hours = 0
    non_green_energy_hours = 0

    print(len(response.json()['data']), len(moer_list))

    green_times: list[str] = []
    for j in range(72 * 12):
        if np.mean(moer_list) - np.std(moer_list)/2 > moer_list[j]:
            print(response.json()['data'][j]['point_time'].split('T')[1])
            green_times.append(response.json()['data'][j]['point_time'].split('T')[1])
            
            print("Green Energy")
            green_energy_hours += 1
        else:
            print("")
            non_green_energy_hours += 1

    for green_time in green_times:
        # Get next green time
        now = datetime.now(timezone(timedelta(hours=0))).isoformat()
        if (datetime.fromisoformat(now[:now.index("T") + 1] + green_time) - datetime.now(timezone(timedelta(hours=0)))).total_seconds() >= 0:
            next_green_time: str = green_time
        else:
            continue

    if (datetime.fromisoformat(now[:now.index("T") + 1] + green_time) - datetime.now(timezone(timedelta(hours=0)))).total_seconds() > battery.secsleft and fetch_charging_status():
        toast.show_toast(
            "Charging Unsustainably",
            "Consider holding off on charging until " + next_green_time,
            duration=20,
            threaded=True,
        )
    if True:# (datetime.fromisoformat(now[:now.index("T") + 1] + green_time) - datetime.now(timezone(timedelta(hours=0)))).total_seconds() <= 0 and not fetch_charging_status() and fetch_percent() < 90:
        toast.show_toast(
            "Sustainable Charging Available",
            "Consider charging now, if possible",
            duration=20,
            threaded=True,
        )
    
    textvar.set(next_green_time)
    plot_graph(range(0, len(moer_list) * 5, 5), moer_list)

    tk.after(60000, get_energy_mix, "GridWise_2025",
             "Grid_Wise_medhansh_rishit_buhhs_2025#", get_location()['loc'], root, textvar)

if __name__ == "__main__":
    root = Tk()
    root.title("GridWise")
    root.geometry("800x600")  # Set the window size as needed

    textvar = StringVar()

    Label(root, text="Next Charging Time (UTC)").pack()

    energy_qual = Label(root, textvariable=textvar)
    energy_qual.pack()

    get_energy_mix("GridWise_2025",
    "Grid_Wise_medhansh_rishit_buhhs_2025#", get_location()[
        'loc'], root, textvar)

    root.mainloop()
