import pandas as pd

input_csv = './output/kafe_di_situbondo_20251229_005525.csv'
output_xlsx = './output/data.xlsx'

try:
    print(f"Membaca file {input_csv}...")
    df = pd.read_csv(input_csv)

    print("Mengkonversi ke Excel...")
    df.to_excel(output_xlsx, index=False)

    print(f"Berhasil! File tersimpan sebagai: {output_xlsx}")

except FileNotFoundError:
    print(f"Error: File '{input_csv}' tidak ditemukan.")
except Exception as e:
    print(f"Terjadi kesalahan: {e}")