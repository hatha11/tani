from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
import paho.mqtt.client as mqtt
from kivy_garden.graph import Graph, LinePlot


# Konfigurasi MQTT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_PUB_TOPIC = "my/kivy/device"
MQTT_SUB_TOPIC = "my/kivy/temperature"

class IoTApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.status_device_label = Label(text="Status: --", font_size=24)
        self.layout.add_widget(self.status_device_label)

        # Data suhu awal
        self.data_suhu = []

        # Grafik suhu
        self.graph = Graph(xlabel='Data ke-', ylabel='Suhu (°C)',
                   x_ticks_minor=1, x_ticks_major=5, y_ticks_major=5,
                   y_grid_label=True, x_grid_label=True,
                   padding=5, x_grid=True, y_grid=True,
                   xmin=0, xmax=20, ymin=0, ymax=50,
                   size_hint=(1, 0.5))

        self.plot = LinePlot(line_width=1.5, color=[1, 0, 0, 1])  # Merah
        self.graph.add_plot(self.plot)

        self.layout.add_widget(self.graph)


        # Label untuk menampilkan suhu
        self.status_label = Label(text="Suhu: -- °C", font_size=28)
        self.layout.add_widget(self.status_label)

        # Tombol ON dan OFF
        btn_on = Button(text='ON', font_size=32)
        btn_off = Button(text='OFF', font_size=32)
        btn_on.bind(on_press=self.kirim_on)
        btn_off.bind(on_press=self.kirim_off)
        self.layout.add_widget(btn_on)
        self.layout.add_widget(btn_off)

        # Setup MQTT Client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)

        # Mulai loop MQTT di thread terpisah
        self.client.loop_start()

        return self.layout

    def kirim_on(self, instance):
        self.client.publish(MQTT_PUB_TOPIC, "ON")
        self.status_device_label.text = "Status: ON"

    def kirim_off(self, instance):
        self.client.publish(MQTT_PUB_TOPIC, "OFF")
        self.status_device_label.text = "Status: OFF"

    def on_connect(self, client, userdata, flags, rc):
        print("Terhubung ke broker dengan kode:", rc)
        client.subscribe(MQTT_SUB_TOPIC)

    def on_message(self, client, userdata, msg):
        suhu = msg.payload.decode("utf-8")
        Clock.schedule_once(lambda dt: self.update_label(suhu))

    def update_label(self, suhu):
        try:
            nilai = float(suhu)
        except ValueError:
            return  # abaikan jika bukan angka

        self.status_label.text = f"Suhu: {suhu} °C"
        self.data_suhu.append(nilai)

        # Batasi hanya 20 data terakhir
        if len(self.data_suhu) > 20:
            self.data_suhu.pop(0)

        # Update grafik
        self.plot.points = [(i, y) for i, y in enumerate(self.data_suhu)]
        self.graph.xmax = max(20, len(self.data_suhu))
        self.graph.ymax = max(50, max(self.data_suhu) + 5)

if __name__ == '__main__':
    IoTApp().run()
