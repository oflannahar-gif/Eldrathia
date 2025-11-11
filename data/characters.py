# =====================================================
# 📜 DATA KARAKTER DUNIA ELDRAHTHIA
# =====================================================

CHARACTERS = {
    "Fighter": [
        {
            "name": "Kael Draven",
            "title": "The Unbroken Blade",
            "class": "Fighter",
            "hp": 120,
            "atk": 18,
            "def": 10,
            "skill": "Berserker Slash",
            "skill_desc": "Menyerang musuh dengan tebasan kuat yang menambah 25% damage.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/KaelDraven.jpeg",
            "desc": (
                "Prajurit kelahiran Arvendale yang dikenal karena keberaniannya menantang pasukan iblis "
                "sendirian di gerbang utara. Luka di bahunya menjadi simbol sumpahnya untuk tidak pernah "
                "mundur dari pertempuran."
            )
        },
        {
            "name": "Riona Valehart",
            "title": "The Steel Maiden",
            "class": "Fighter",
            "hp": 115,
            "atk": 20,
            "def": 9,
            "skill": "Valiant Strike",
            "skill_desc": "Serangan cepat beruntun yang meningkatkan critical chance sebesar 15% selama 2 giliran.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/RionaValehart.jpeg",
            "desc": (
                "Putri seorang pandai besi legendaris yang menolak hidup nyaman di istana. "
                "Riona menempah sendiri pedangnya, 'Valkryn', dan bersumpah melindungi rakyat lemah "
                "dari tirani perang."
            )
        },
    ],

    "Mage": [
        {
            "name": "Ardyn Velas",
            "title": "The Timebinder",
            "class": "Mage",
            "hp": 90,
            "atk": 25,
            "def": 6,
            "skill": "Chrono Flare",
            "skill_desc": "Melepaskan ledakan energi waktu yang memberi 30% magic damage dan memperlambat musuh selama 1 giliran.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/ArdynVelas.jpeg",
            "desc": (
                "Penyihir muda dari Menara Eldrath yang kehilangan kendali atas kekuatan waktu. "
                "Ia kini mencari cara menebus kesalahan yang membuat separuh gurunya terperangkap di masa lalu."
            )
        },
        {
            "name": "Lyra Merenis",
            "title": "The Starweaver",
            "class": "Mage",
            "hp": 85,
            "atk": 27,
            "def": 5,
            "skill": "Starlight Nova",
            "skill_desc": "Menyerang seluruh musuh dengan cahaya kosmik, menimbulkan 20% area damage dan menurunkan magic resist musuh.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/LyraMerenis.jpeg",
            "desc": (
                "Dikenal sebagai 'Sang Penenun Bintang', Lyra mampu memanggil cahaya kosmos di tengah malam. "
                "Meski lembut, kekuatannya pernah menghancurkan pasukan iblis dalam satu mantra."
            )
        },
    ],

    "Assassin": [
        {
            "name": "Sylas Corvin",
            "title": "The Silent Redeemer",
            "class": "Assassin",
            "hp": 95,
            "atk": 24,
            "def": 7,
            "skill": "Shadow Reap",
            "skill_desc": "Menyerang dari bayangan, memberikan 35% damage tambahan jika musuh sedang terkena debuff.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/SylasCorvin.jpeg",
            "desc": (
                "Mantan pembunuh bayaran dari bawah tanah Eldrathia. Kini ia menebus masa lalunya dengan memburu "
                "mereka yang dulu membayar jasanya untuk membunuh orang tak bersalah."
            )
        },
        {
            "name": "Nyra Vexen",
            "title": "The Shadow of Umbravale",
            "class": "Assassin",
            "hp": 90,
            "atk": 26,
            "def": 6,
            "skill": "Silent Veil",
            "skill_desc": "Menghilang selama 1 giliran, meningkatkan peluang critical dan menghindari serangan berikutnya.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/NyraVexen.jpeg",
            "desc": (
                "Bayangan tanpa suara dari Kerajaan Umbravale. Nyra tak pernah terlihat dua kali oleh target "
                "yang sama — sebagian percaya ia hanya legenda yang diciptakan untuk menakuti pengkhianat."
            )
        },
    ],

    "Paladin": [
        {
            "name": "Darius Lumehart",
            "title": "The Lightbringer",
            "class": "Paladin",
            "hp": 140,
            "atk": 16,
            "def": 14,
            "skill": "Divine Judgment",
            "skill_desc": "Memanggil cahaya suci untuk menyerang musuh dan memulihkan 10% HP sekutu di sekitarnya.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/DariusLumehart.jpeg",
            "desc": (
                "Ksatria suci yang memimpin pasukan cahaya di bawah panji Arvendale. "
                "Setiap kali Solmere bersinar di tangannya, keputusasaan musuh berubah menjadi debu keheningan."
            )
        },
        {
            "name": "Elenya Crestborne",
            "title": "The Divine Shield",
            "class": "Paladin",
            "hp": 130,
            "atk": 15,
            "def": 15,
            "skill": "Holy Aegis",
            "skill_desc": "Menciptakan perisai cahaya yang menyerap 20% damage dan memantulkannya ke musuh.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/ElenyaCrestborne.jpeg",
            "desc": (
                "Paladin wanita yang memimpin Ordo Cahaya setelah kematian ayahnya di medan perang. "
                "Ia dikenal karena keberanian dan doa sucinya yang mampu menghidupkan semangat seluruh pasukan."
            )
        },
    ],

    "Tank": [
        {
            "name": "Thoran Brackmoor",
            "title": "The Mountain Wall",
            "class": "Tank",
            "hp": 180,
            "atk": 12,
            "def": 20,
            "skill": "Iron Fortress",
            "skill_desc": "Memperkuat pertahanan selama 2 giliran dan menarik musuh untuk menyerang dirinya.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/ThoranBrackmoor.jpeg",
            "desc": (
                "Raksasa berhati lembut dari pegunungan Frostheim. Ia menangkis serangan naga sendirian "
                "untuk memberi waktu rakyatnya melarikan diri — dan sejak itu, tak satu pun perisai mampu "
                "menyaingi miliknya."
            )
        },
        {
            "name": "Mira Halvren",
            "title": "The Living Bulwark",
            "class": "Tank",
            "hp": 170,
            "atk": 13,
            "def": 18,
            "skill": "Guardian’s Stand",
            "skill_desc": "Membentuk medan pelindung yang mengurangi 25% damage yang diterima sekutu selama 1 giliran.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/MiraHalvren.jpeg",
            "desc": (
                "Seorang penjaga kota tua yang kini menjadi benteng hidup bagi rekan-rekannya. "
                "Tubuhnya penuh luka, tapi setiap bekasnya adalah cerita pengorbanan demi melindungi yang ia cintai."
            )
        },
    ],

    "Archer": [
        {
            "name": "Eryndor Kaelis",
            "title": "The Windstrider",
            "class": "Archer",
            "hp": 110,
            "atk": 21,
            "def": 9,
            "skill": "Hawkshot",
            "skill_desc": "Menembakkan panah presisi tinggi yang memiliki peluang 30% untuk menembus pertahanan musuh.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/EryndorKaelis.jpeg",
            "desc": (
                "Penjaga hutan Eldrath yang legendaris. Panahnya selalu mengenai sasaran bahkan tanpa terlihat "
                "dilepaskan. Ia lebih mempercayai bisikan angin daripada suara manusia."
            )
        },
        {
            "name": "Sylwen Aramir",
            "title": "The Elven Sentinel",
            "class": "Archer",
            "hp": 105,
            "atk": 22,
            "def": 8,
            "skill": "Nature’s Whisper",
            "skill_desc": "Memanggil kekuatan hutan untuk menyerang musuh dan memulihkan sedikit HP dirinya.",
            "image": "https://cobacoba123.my.id/Eldrathia/MainCharacter/SylwenAramir.jpeg",
            "desc": (
                "Penembak jitu dari kaum Elf yang menjaga batas antara dunia manusia dan hutan kuno. "
                "Setiap anak panahnya membawa doa bagi alam yang ia lindungi."
            )
        },
    ],
}
