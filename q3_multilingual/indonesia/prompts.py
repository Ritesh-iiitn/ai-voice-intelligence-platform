"""
Localized Indonesian voice agent dialogue templates for formal and colloquial registers.
"""

ID_PROMPTS = {
    "greeting": (
        "Halo, selamat siang! Saya Alex dari Apex Pembiayaan dan Kredit Kendaraan. "
        "Saya ingin menindaklanjuti pengajuan fasilitas pembiayaan pre-approval Anda. "
        "Apakah benar saya berbicara dengan Bapak/Ibu {name}?"
    ),
    "consent_request": (
        "Terima kasih. Sebelum kita lanjutkan untuk meninjau simulasi cicilan dan tenor Anda, "
        "percakapan ini kami rekam untuk keperluan kualitas pelayanan dan kepatuhan regulasi. "
        "Apakah Bapak/Ibu bersedia untuk melanjutkan?"
    ),
    "consent_declined": (
        "Baik, saya sangat memahami. Karena kepatuhan regulasi perbankan mewajibkan rekaman suara untuk penawaran via telepon, "
        "kami tidak dapat melanjutkan melalui panggilan ini. Kami dapat mengirimkan rincian simulasi melalui WhatsApp atau email resmi."
    ),
    "ask_amount": (
        "Baik. Berapa perkiraan jumlah dana pembiayaan yang Bapak/Ibu rencanakan untuk diajukan?"
    ),
    "ask_income": (
        "Baik, dicatat. Dan untuk verifikasi rasio angsuran, berapa rata-rata penghasilan bersih per bulan yang Bapak/Ibu terima saat ini?"
    ),
    "ask_credit_score": (
        "Terima kasih. Terakhir, apakah Bapak/Ibu mengetahui riwayat skor kredit atau kelancaran SLIK OJK sebelumnya?"
    ),
    "objection_bunga_tinggi": (
        "Saya sangat mengerti pertimbangan Bapak/Ibu. Keunggulan utama pembiayaan kami adalah suku bunga tetap (fixed APR) "
        "mulai dari 6.49% per tahun, dan yang terpenting adalah bebas denda pelunasan dipercepat (0% penalty). "
        "Artinya Bapak/Ibu bisa melunasi sisa pokok kapan saja tanpa biaya tambahan untuk menghemat total bunga."
    ),
    "tenor_dan_denda_info": (
        "Fasilitas kami menyediakan pilihan tenor fleksibel mulai dari 12 hingga 72 bulan. "
        "Untuk denda keterlambatan, ada masa tenggang (grace period) selama 7 hari, dan tidak ada denda penalti untuk pelunasan lebih awal."
    ),
    "unsupported_fallback": (
        "Mohon maaf, saya belum memiliki informasi resmi mengenai hal tersebut di dalam panduan pembiayaan kami. "
        "Saya dapat menghubungkan Bapak/Ibu dengan representatif spesialis kredit kami untuk penjelasan lebih lanjut."
    ),
    "escalation_transfer": (
        "Baik, saya menghentikan proses otomatis ini dan segera menghubungkan Bapak/Ibu dengan representatif petugas kami. "
        "Mohon tetap berada di sambungan telepon."
    ),
    "wrapup_qualified": (
        "Kabar gembira! Berdasarkan analisis awal, pengajuan pembiayaan Bapak/Ibu memenuhi syarat untuk {tier_name} "
        "dengan suku bunga tetap {apr} per tahun dan bebas denda pelunasan awal. Nomor referensi pengajuan Anda adalah: {lead_id}."
    ),
    "wrapup_disqualified": (
        "Terima kasih atas waktu Bapak/Ibu. Untuk saat ini profil penghasilan belum memenuhi ambang batas minimum "
        "sebesar Rp 38.000.000 per bulan atau skor kredit 650. Kami akan mengirimkan panduan perbaikan skor kredit ke kontak Anda."
    )
}
