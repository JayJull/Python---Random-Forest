from lib.scrap.interfaceScrap import BusinessData, SendFn, DatabaseCounter


async def save_business_to_database(
    item:     BusinessData,
    location: str,
    category: str,
    send:     SendFn,
    counter:  DatabaseCounter,
    Lead,
) -> None:
    try:
        exists = await Lead.find_one({"nama": item.business_name, "lokasi": location})

        if exists:
            counter.skipped += 1
            return

        await Lead.create({
            "nama":         item.business_name,
            "rating":       item.rating,
            "jumlahUlasan": item.review_count,
            "noTelp":       item.phone,
            "alamat":       item.address,
            "mapsUrl":      item.maps_url,
            "keterangan":   "",
            "status":       "Belum Diproses",
            "keyword":      category,
            "lokasi":       location,
        })

        counter.saved += 1
        send("success", f"Tersimpan ke database: {item.business_name}")

    except Exception as err:
        send("error", f'Gagal menyimpan "{item.business_name}": {err}')