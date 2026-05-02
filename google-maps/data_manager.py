"""
data_manager.py
Mengelola penyimpanan dan ekspor data hasil scraping
"""

import pandas as pd
import os
from datetime import datetime
import config
import utils

class DataManager:
    """
    Class untuk mengelola penyimpanan data hasil scraping
    """
    
    def __init__(self):
        self.data = []
        self._ensure_output_folder()
    
    def _ensure_output_folder(self):
        """
        Memastikan folder output ada
        """
        if not os.path.exists(config.OUTPUT_FOLDER):
            os.makedirs(config.OUTPUT_FOLDER)
            utils.log_message(f"Folder '{config.OUTPUT_FOLDER}' dibuat")
    
    def save_to_csv(self, data, search_query):
        """
        Menyimpan data ke file CSV
        
        Args:
            data: List dictionary berisi data bisnis
            search_query: Query pencarian untuk nama file
        
        Returns:
            str: Path file yang disimpan
        """
        if not data:
            utils.log_message("Tidak ada data untuk disimpan", "WARNING")
            return None
        
        try:
            # Buat DataFrame
            df = pd.DataFrame(data)
            
            # Tambah kolom metadata
            df['keyword_pencarian'] = search_query
            
            # Urutkan kolom
            column_order = [
                'nama_bisnis',
                'kategori',
                'rating',
                'jumlah_ulasan',
                'no_telepon',
                'website',
                'alamat',
                'status_prospek',
                'skor_prospek',
                'alasan',
            ]

            # Tambahkan kolom klasifikasi jika belum ada (backward compatible)
            for col in ['status_prospek', 'skor_prospek', 'alasan']:
                if col not in df.columns:
                    df[col] = ''
            
            df = df[column_order]
            
            # Generate nama file dengan timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c for c in search_query if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_query = safe_query.replace(' ', '_')[:30]
            
            filename = f"{safe_query}_{timestamp}.csv"
            filepath = os.path.join(config.OUTPUT_FOLDER, filename)
            
            # Simpan ke CSV
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            utils.log_message(f"✓ Data berhasil disimpan ke: {filepath}")
            utils.log_message(f"  Total data: {len(df)} baris")
            
            return filepath
        
        except Exception as e:
            utils.log_message(f"Error menyimpan data: {str(e)}", "ERROR")
            return None
    
    def print_summary(self, data):
        """
        Menampilkan ringkasan data yang dikumpulkan
        
        Args:
            data: List dictionary berisi data bisnis
        """
        if not data:
            utils.log_message("Tidak ada data untuk ditampilkan", "WARNING")
            return
        
        utils.log_message("\n" + "="*60)
        utils.log_message("RINGKASAN DATA SCRAPING")
        utils.log_message("="*60)
        
        df = pd.DataFrame(data)
        
        # Statistik klasifikasi prospek
        if 'status_prospek' in df.columns:
            utils.log_message("\nHasil Klasifikasi Prospek:")
            status_counts = df['status_prospek'].value_counts()
            for status, count in status_counts.items():
                emoji = '🔥' if 'Hot' in status else ('🌡' if 'Warm' in status else '❄')
                utils.log_message(f"  {emoji} {status}: {count} bisnis")

        # Statistik umum
        utils.log_message(f"Total bisnis terkumpul: {len(df)}")
        utils.log_message(f"Bisnis dengan telepon: {df['no_telepon'].notna().sum()}")
        utils.log_message(f"Bisnis dengan website: {df['website'].notna().sum()}")
        
        # Statistik rating
        if 'rating' in df.columns:
            avg_rating = df[df['rating'] > 0]['rating'].mean()
            utils.log_message(f"Rata-rata rating: {avg_rating:.2f}")
        
        # Kategori terbanyak
        if 'kategori' in df.columns:
            top_categories = df['kategori'].value_counts().head(5)
            utils.log_message("\nTop 5 Kategori:")
            for cat, count in top_categories.items():
                utils.log_message(f"  - {cat}: {count} bisnis")
        
        # Preview data
        utils.log_message("\nPreview Data (5 baris pertama):")
        utils.log_message("-"*60)
        
        for i, row in df.head(5).iterrows():
            utils.log_message(f"\n{i+1}. {row['nama_bisnis']}")
            utils.log_message(f"   Kategori: {row['kategori']}")
            utils.log_message(f"   Rating: {row['rating']} ({row['jumlah_ulasan']} ulasan)")
            utils.log_message(f"   Telepon: {row['no_telepon'] if row['no_telepon'] else 'Tidak ada'}")
        
        utils.log_message("\n" + "="*60)
    
    def validate_data(self, data):
        """
        Validasi kualitas data yang dikumpulkan
        
        Args:
            data: List dictionary berisi data bisnis
        
        Returns:
            dict: Laporan validasi
        """
        if not data:
            return {
                'valid': False,
                'message': 'Tidak ada data'
            }
        
        df = pd.DataFrame(data)
        
        # Hitung kelengkapan data
        completeness = {
            'nama_bisnis': (df['nama_bisnis'].notna() & (df['nama_bisnis'] != '')).sum(),
            'kategori': (df['kategori'].notna() & (df['kategori'] != '')).sum(),
            'rating': (df['rating'] > 0).sum(),
            'no_telepon': (df['no_telepon'].notna() & (df['no_telepon'] != '')).sum(),
            'website': (df['website'].notna() & (df['website'] != '')).sum(),
            'alamat': (df['alamat'].notna() & (df['alamat'] != '')).sum()
        }
        
        total_rows = len(df)
        completeness_percent = {k: (v/total_rows)*100 for k, v in completeness.items()}
        
        # Data dianggap valid jika minimal 80% memiliki nama dan kategori
        is_valid = (completeness_percent['nama_bisnis'] >= 80 and 
                   completeness_percent['kategori'] >= 80)
        
        return {
            'valid': is_valid,
            'total_rows': total_rows,
            'completeness': completeness,
            'completeness_percent': completeness_percent
        }