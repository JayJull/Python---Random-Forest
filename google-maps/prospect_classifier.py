import utils
WEIGHT_ULASAN  = 0.623
WEIGHT_RATING  = 0.332
WEIGHT_WEBSITE = 0.045

ULASAN_ZONES = [
    (29,  1.0),
    (50,  0.6),
    (100, 0.2),
]

RATING_ZONES = [
    (4.9, 1.0),
    (4.8, 0.4),
    (4.5, 0.1),
]

THRESHOLD_HOT = 0.50


def _score_ulasan(jumlah_ulasan: int) -> float:
    for batas, skor in ULASAN_ZONES:
        if jumlah_ulasan <= batas:
            return skor
    return 0.0


def _score_rating(rating: float) -> float:
    for batas, skor in RATING_ZONES:
        if rating >= batas:
            return skor
    return 0.0


def classify_prospect(business_data: dict) -> dict:
    jumlah_ulasan = int(business_data.get('jumlah_ulasan') or 0)
    rating        = float(business_data.get('rating') or 0.0)
    website_raw   = str(business_data.get('website', '') or '')
    no_telepon    = str(business_data.get('no_telepon', '') or '')

    # Gate: tanpa nomor telepon tidak bisa dihubungi → Cold langsung
    if no_telepon.strip() in ('', '0', 'nan'):
        return {
            **business_data,
            'status_prospek': 'Cold Prospek',
            'skor_prospek':   0.0,
            'alasan':         'Tidak ada nomor telepon — tidak bisa dihubungi'
        }

    s_ulasan  = _score_ulasan(jumlah_ulasan)
    s_rating  = _score_rating(rating)
    s_website = 1.0 if website_raw in ('', '0') else 0.0

    total_score = round(
        (s_ulasan  * WEIGHT_ULASAN) +
        (s_rating  * WEIGHT_RATING) +
        (s_website * WEIGHT_WEBSITE),
        3
    )

    detail = (
        f"({s_ulasan}×0.623) + ({s_rating}×0.332) + ({s_website:.0f}×0.045) = {total_score}"
    )

    if total_score >= THRESHOLD_HOT:
        status = 'Hot Prospek'
        alasan = f"Skor {detail} ≥ 0.50 — ulasan sedikit ({jumlah_ulasan}) + rating tinggi ({rating})"
    else:
        status = 'Cold Prospek'
        if jumlah_ulasan > 100:
            note = f"ulasan {jumlah_ulasan} sudah banyak (> Cold median=124)"
        elif rating < 4.5:
            note = f"rating {rating} rendah (< Cold mean=4.61)"
        else:
            note = "kombinasi ulasan+rating tidak cukup"
        alasan = f"Skor {detail} < 0.50 — {note}"

    return {
        **business_data,
        'status_prospek': status,
        'skor_prospek':   total_score,
        'alasan':         alasan
    }


def classify_all(data_list: list) -> list:
    """
    Klasifikasikan seluruh daftar bisnis hasil scraping.

    Args:
        data_list: list of dict dari scraper

    Returns:
        list of dict dengan tambahan 'status_prospek', 'skor_prospek', 'alasan'
    """
    results = []
    hot_count = cold_count = 0

    for business in data_list:
        classified = classify_prospect(business)
        results.append(classified)

        status = classified['status_prospek']
        nama   = classified.get('nama_bisnis', '-')
        ul     = classified.get('jumlah_ulasan', 0)
        rt     = classified.get('rating', 0)
        skor   = classified['skor_prospek']

        if status == 'Hot Prospek':
            hot_count += 1
            utils.log_message(f"HOT  [skor={skor}] {nama} | ulasan={ul} | rating={rt}")
        else:
            cold_count += 1
            utils.log_message(f"COLD [skor={skor}] {nama} | ulasan={ul} | rating={rt}")

    utils.log_message(
        f"\n📊 Klasifikasi selesai: "
        f"Hot={hot_count}  Cold={cold_count}  Total={len(results)}"
    )
    return results