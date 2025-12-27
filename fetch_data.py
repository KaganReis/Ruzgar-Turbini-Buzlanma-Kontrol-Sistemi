import json
import urllib.request
import pandas as pd
from datetime import datetime, timedelta

def gercek_verileri_getir():
    print("🌍 Open-Meteo Servisine Bağlanılıyor (ERZURUM - 3 YILLIK VERİ)...")
    
    # 1. AYARLAR
    # Erzurum Koordinatları
    latitude = 39.9043
    longitude = 41.2679
    
    # Tarih Hesaplama (Bugünden geriye 3 YIL = 1095 gün)
    bugun = datetime.now()
    baslangic_tarihi = (bugun - timedelta(days=1095)).strftime('%Y-%m-%d')
    bitis_tarihi = (bugun - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # API URL'si
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}&start_date={baslangic_tarihi}&end_date={bitis_tarihi}&hourly=temperature_2m"
    
    try:
        # 2. VERİYİ İNDİR (İnternetten)
        with urllib.request.urlopen(url) as response:
            veri_json = json.loads(response.read().decode())
            
        print("✅ Veri başarıyla indirildi. İşleniyor...")
        
        saatlik_veri = veri_json["hourly"]
        zamanlar = saatlik_veri["time"]
        sicakliklar = saatlik_veri["temperature_2m"]
        
        # 3. CSV FORMATINA DÖNÜŞTÜR
        yeni_veri_listesi = []
        
        for i in range(len(zamanlar)):
            # Zaman formatı: "2023-12-25T00:00" -> Ayırıp gün ve saati alacağız
            tarih_saat = zamanlar[i]
            dt_object = datetime.strptime(tarih_saat, "%Y-%m-%dT%H:%M")
            
            # Veri setimiz için basitleştirilmiş "Gun" sayısı (1'den 7'ye kadar)
            # (Basitlik olsun diye gün farkını alıyoruz)
            ilk_gun = datetime.strptime(zamanlar[0], "%Y-%m-%dT%H:%M")
            gun_sirasi = (dt_object - ilk_gun).days + 1
            
            saat = dt_object.hour
            sicaklik = sicakliklar[i]
            
            # Durum Belirleme
            durum = "Normal"
            if sicaklik <= 0:
                durum = "Buzlanma"
            elif sicaklik <= 4:
                durum = "Buzlanma Riski"
                
            yeni_veri_listesi.append({
                "gun": gun_sirasi,
                "saat": saat,
                "sicaklik": sicaklik,
                "durum": durum
            })
            
        # 4. DOSYAYA KAYDET
        df = pd.DataFrame(yeni_veri_listesi)
        df.to_csv("weather_data.csv", index=False)
        
        print(f"✅ 'weather_data.csv' dosyası başarıyla oluşturuldu!")
        print(f"📊 Toplam {len(yeni_veri_listesi)} saatlik veri işlendi.")
        print(f"ℹ️  Konum: {latitude}, {longitude}")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")

if __name__ == "__main__":
    gercek_verileri_getir()
