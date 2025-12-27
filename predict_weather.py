import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import sys
import os
import joblib 
import serial 
import time

def tahmin_et(dosya_yolu):
    model_dosyasi = "egitilmis_beyin.pkl" 
    
    # ARDUINO AYARLARI 
    ARDUINO_PORT = "/dev/tty.usbserial-130" 
    BAUD_RATE = 9600

    print(f"Veriler '{dosya_yolu}' dosyasından yükleniyor...")
    
    try:
        # 1. Veriyi Oku ve Tahmin Yap (Başlangıçta 1 Kere)
        veri = pd.read_csv(dosya_yolu)
        
        son_30_gun_saatleri = 30 * 24
        egitim_verisi = veri.tail(son_30_gun_saatleri)
        X = egitim_verisi[['gun', 'saat']] 
        y = egitim_verisi['sicaklik']

        print(f"Model eğitiliyor...")
        model = LinearRegression()
        model.fit(X, y)
        joblib.dump(model, model_dosyasi)
        
        # Geleceği Tahmin Et
        son_gun = veri['gun'].max()
        yarin = son_gun + 1
        buzlanma_riski_var_mi = False
        
        print("-" * 30)
        print(f"RAPOR: {yarin}. GÜN TAHMİNİ")
        
        for saat in range(0, 24):
            tahmin_verisi = pd.DataFrame({'gun': [yarin], 'saat': [saat]})
            tahmin_sicaklik = model.predict(tahmin_verisi)[0]
            if tahmin_sicaklik <= 0:
                buzlanma_riski_var_mi = True
        
        # Risk Durumunu Ekrana Bas
        if buzlanma_riski_var_mi:
             print("⚠️  GENEL SONUÇ: Yarın buzlanma riski VAR! ❄️")
        else:
             print("✅ GENEL SONUÇ: Yarın buzlanma riski YOK.")

        # ----------------------------------------------------------------
        # SÜREKLİ TAKİP MODU (LOOP)
        # ----------------------------------------------------------------
        print("-" * 30)
        print("Mesafe Sensörü ve Alarm Sistemi Başlatılıyor...")
        print("Motorun durmaması için programı KAPATMAYIN. (Çıkış için Ctrl+C)")
        
        ser = None
        try:
            # Bağlantıyı 1 Kere Aç
            ser = serial.Serial()
            ser.port = ARDUINO_PORT
            ser.baudrate = BAUD_RATE
            ser.timeout = 2
            ser.dtr = False 
            ser.rts = False 
            ser.open()
            time.sleep(2) # İlk açılış resetini bekle
            ser.reset_input_buffer()
            print("🔌 Arduino Bağlandı! Şimdi sürekli izleniyor...")
            
        except Exception as e_ser:
            print(f"⚠️ Arduino Bağlantı Hatası: {e_ser}")
            return False

        # SONSUZ DÖNGÜ
        son_durum_riskli_mi = None # Başlangıçta bilinmiyor

        while True:
            try:
                # 1. Eğer yapay zeka risk yok dediyse
                if not buzlanma_riski_var_mi:
                     if son_durum_riskli_mi is not False:
                         ser.write(b'0')
                         son_durum_riskli_mi = False
                         print("\n✅ Yapay Zeka Risk Görmüyor -> Güvenli Mod Aktif.")
                     
                     time.sleep(5) 
                     continue

                # 2. Risk Varsa: Sensörü Oku (Hızlı Güncelleme: 5 Örnek)
                ornekler = []
                # Arduino tarafı 50ms'de bir gönderiyor.
                # 5 örnek okumak yaklaşık 250ms sürer. 
                for _ in range(5): 
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        try:
                            val = float(line)
                            ornekler.append(val)
                        except:
                            pass
                    # time.sleep(0.05) <- KALDIRILDI (Hız için) 
                
                if len(ornekler) > 0:
                    avg_mesafe = sum(ornekler) / len(ornekler)
                    print(f"📏 Mesafe (Ort): {avg_mesafe:.1f} cm   ", end="\r") 
                    
                    if avg_mesafe < 4.0:
                        # RİSK + SENSÖR = ALARM
                        # Sadece daha önce "Güvenli" moddaysak veya ilk kez ise tetikle
                        # (Böylece sürekli '1' gönderip buzzer zamanlayıcısını sıfırlamayız)
                        if son_durum_riskli_mi is not True:
                            ser.write(b'1')
                            son_durum_riskli_mi = True
                            print(f"\n❄️  BUZLANMA TESPİT EDİLDİ! ({avg_mesafe:.1f} cm) -> ALARM 🚨")
                        
                    else:
                        # RİSK VAR AMA SENSÖR TEMİZ
                        if son_durum_riskli_mi is not False:
                            ser.write(b'0')
                            son_durum_riskli_mi = False
                            print(f"\n👍 Fiziksel Ortam Temiz ({avg_mesafe:.1f} cm) -> Güvenli Mod")
                        
                else:
                     pass

                time.sleep(0.1) # Döngü hızı

            except KeyboardInterrupt:
                print("\nProgram kullanıcı tarafından durduruldu.")
                break
            except Exception as e_loop:
                print(f"\nDöngü Hatası: {e_loop}")
                time.sleep(1)

        if ser and ser.is_open:
            ser.close()
            print("Port kapatıldı.")

        return True

    except Exception as e:
        print(f"Genel Hata: {e}")
        return None

if __name__ == "__main__":
    dosya = "weather_data.csv"
    tahmin_et(dosya)
