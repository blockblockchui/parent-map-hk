// 50個親子地點 - 完整資料 (精簡版)
// verified: true = 人手驗證 | false = 自動搜集未驗證
// autoDiscovered: true = Scout 自動發現

export const locations = [
  {
    id: "001", name: "樹屋 Baumhaus", district: "灣仔", region: "hk-island",
    lat: 22.2755, lng: 114.1708, category: "playhouse", indoor: true,
    ageRange: [0, 6], priceType: "medium", priceDescription: "$100-200",
    description: "木製遊樂空間，提供創意藝術課程及探索樹屋",
    website: "https://www.baumhaus.com.hk/", tips: "建議預約",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "灣仔 Queen's Road East 36-44號"
  },
  {
    id: "002", name: "Ryze Hong Kong", district: "鰂魚涌", region: "hk-island",
    lat: 22.2876, lng: 114.2120, category: "playhouse", indoor: true,
    ageRange: [2, 12], priceType: "high", priceDescription: "$200-400",
    description: "高能量蹦床公園，設有互聯蹦床、障礙課程",
    website: "https://www.ryzehongkong.com/", tips: "適合好動小朋友",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "鰂魚涌 Java Road 321號"
  },
  {
    id: "003", name: "Sooper Yoo", district: "堅尼地城", region: "hk-island",
    lat: 22.2815, lng: 114.1265, category: "playhouse", indoor: true,
    ageRange: [3, 12], priceType: "medium", priceDescription: "$100-200",
    description: "科技融入運動區，設有互動遊戲、F1式賽車",
    website: "https://www.sooperyoo.com/", tips: "科技感十足",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "堅尼地城 Belcher's Street 8號"
  },
  {
    id: "004", name: "Kiztopia", district: "多分店", region: "kowloon",
    lat: 22.3025, lng: 114.1785, category: "playhouse", indoor: true,
    ageRange: [1, 12], priceType: "medium", priceDescription: "$100-200",
    description: "教育娛樂遊樂場，設有主題區、滑梯、蹦床",
    website: "https://kiztopia.com.hk/", tips: "多間分店",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: true,
    openingHours: "10:00-20:00", address: "灣仔/將軍澳/沙田/奧海城"
  },
  {
    id: "005", name: "Super Sports Park", district: "大角咀", region: "kowloon",
    lat: 22.3175, lng: 114.1605, category: "playhouse", indoor: true,
    ageRange: [3, 12], priceType: "high", priceDescription: "$200-400",
    description: "大型運動主題遊樂場，設有蹦床、攀岩牆",
    website: "https://www.supersportspark.com/", tips: "運動量大",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "大角咀 Hoi Fai Road 18號"
  },
  {
    id: "006", name: "樂高探索中心", district: "尖沙咀", region: "kowloon",
    lat: 22.2942, lng: 114.1745, category: "museum", indoor: true,
    ageRange: [2, 12], priceType: "high", priceDescription: "$200-400",
    description: "樂高主題中心，設有香港微型複製品、4D電影",
    website: "https://www.legolanddiscoverycentre.com/hong-kong/", tips: "樂高迷必去",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: true,
    openingHours: "10:00-19:00", address: "尖沙咀 K11 MUSEA B1層"
  },
  {
    id: "007", name: "Playdot", district: "銅鑼灣", region: "hk-island",
    lat: 22.2795, lng: 114.1830, category: "playhouse", indoor: true,
    ageRange: [0, 12], priceType: "medium", priceDescription: "$100-200",
    description: "自然靈感環保遊樂空間，設有感官區、攀爬",
    website: "https://www.leegardens.com.hk/", tips: "環保主題",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "銅鑼灣 Lee Garden Two 18樓"
  },
  {
    id: "008", name: "Wise-Kids", district: "中環/銅鑼灣", region: "hk-island",
    lat: 22.2830, lng: 114.1550, category: "playhouse", indoor: true,
    ageRange: [0, 6], priceType: "medium", priceDescription: "$100-200",
    description: "明亮遊樂室，設有輪換木製玩具、創意角落",
    website: "https://www.wisekidsplayroom.com/", tips: "注重創意發展",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "中環/銅鑼灣"
  },
  {
    id: "009", name: "EpicLand", district: "啟德/愉景灣", region: "kowloon",
    lat: 22.3305, lng: 114.2030, category: "playhouse", indoor: true,
    ageRange: [2, 12], priceType: "high", priceDescription: "$200-400",
    description: "冒險主題公園，設有巨型滑梯、障礙課程",
    website: "https://www.epiclandhk.com/", tips: "場地很大",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "啟德體育園/愉景灣"
  },
  {
    id: "010", name: "Momoland", district: "多分店", region: "kowloon",
    lat: 22.3145, lng: 114.1670, category: "playhouse", indoor: true,
    ageRange: [2, 12], priceType: "medium", priceDescription: "$100-200",
    description: "主題遊樂屋，設有忍者迷宮、角色扮演區",
    website: "https://momoland.com.hk/", tips: "角色扮演為主",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "荃灣/坑口/北角/將軍澳"
  },
  // 香港科學館系列
  {
    id: "011", name: "香港科學館", district: "尖沙咀", region: "kowloon",
    lat: 22.3015, lng: 114.1790, category: "museum", indoor: true,
    ageRange: [3, 12], priceType: "free", priceDescription: "免費",
    description: "互動式科學展覽，小朋友可以動手體驗科學原理",
    website: "https://hk.science.museum", tips: "建議平日去，周三休館",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "10:00-19:00（周三休）", address: "尖沙咀科學館道2號", phone: "2732 3232"
  },
  {
    id: "012", name: "香港太空館", district: "尖沙咀", region: "kowloon",
    lat: 22.2956, lng: 114.1723, category: "museum", indoor: true,
    ageRange: [4, 12], priceType: "low", priceDescription: "$10-32",
    description: "蛋形建築，天象廳播放星空節目，宇宙展覽",
    website: "https://hk.space.museum", tips: "天象廳要預先買票",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "13:00-21:00（周二休）", address: "尖沙咀梳士巴利道10號", phone: "2721 0226"
  },
  {
    id: "013", name: "香港動植物公園", district: "中環", region: "hk-island",
    lat: 22.2783, lng: 114.1555, category: "park", indoor: false,
    ageRange: [0, 12], priceType: "free", priceDescription: "免費",
    description: "中環綠洲，有紅鸛、狐猴，大草坪適合奔跑",
    website: "https://www.lcsd.gov.hk", tips: "推嬰兒車要小心斜路",
    hasBabyRoom: true, hasStrollerAccess: false, hasRestaurant: true, rainyDaySuitable: false,
    openingHours: "05:00-22:00", address: "中環雅賓利道", phone: "2530 0154"
  },
  {
    id: "014", name: "The Big Things", district: "荃灣", region: "nt",
    lat: 22.3756, lng: 114.1094, category: "playhouse", indoor: true,
    ageRange: [1, 6], priceType: "medium", priceDescription: "$160起",
    description: "自然主題叢林公園，木粒沙池、繩網",
    website: "https://www.thebigthings.com", tips: "記得帶襪",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: true,
    openingHours: "10:00-18:00", address: "荃灣南豐紗廠", phone: "3619 0633"
  },
  {
    id: "015", name: "香港濕地公園", district: "天水圍", region: "nt",
    lat: 22.4667, lng: 114.0083, category: "park", indoor: true,
    ageRange: [3, 12], priceType: "low", priceDescription: "$15-30（周三免費）",
    description: "濕地生態展覽，觀鳥屋、紅樹林步道",
    website: "https://www.wetlandpark.gov.hk", tips: "帶望遠鏡觀鳥",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: true,
    openingHours: "10:00-17:00（周一休）", address: "天水圍濕地公園路", phone: "3152 2666"
  },
  {
    id: "016", name: "JOYPOLIS SPORTS", district: "啟德", region: "kowloon",
    lat: 22.3260, lng: 114.1980, category: "playhouse", indoor: true,
    ageRange: [3, 12], priceType: "high", priceDescription: "$200-400",
    description: "運動娛樂綜合體，忍者課程、VR運動",
    website: "https://hk-joypolis-sports.com", tips: "啟德體育園最新設施",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "啟德體育園健康中心"
  },
  {
    id: "017", name: "KidZania", district: "大嶼山", region: "nt",
    lat: 22.3160, lng: 113.9360, category: "playhouse", indoor: true,
    ageRange: [3, 12], priceType: "high", priceDescription: "$200-400",
    description: "迷你城市，角色扮演職業體驗",
    website: "https://www.kidzania.com.hk", tips: "11 SKIES 商場內",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: true,
    openingHours: "請查詢官網", address: "航天城東路8號 11 SKIES"
  },
  {
    id: "018", name: "Nobi Nobi", district: "將軍澳", region: "nt",
    lat: 22.3070, lng: 114.2600, category: "playhouse", indoor: true,
    ageRange: [0, 12], priceType: "medium", priceDescription: "$100-200",
    description: "大型室內遊樂場，設有幻燈城堡、繩網",
    website: "https://www.nobinobihk.com", tips: "將軍澳中心商場",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: false, rainyDaySuitable: true,
    openingHours: "10:00-21:00", address: "將軍澳唐德街9號"
  },
  {
    id: "019", name: "Snoopy World", district: "沙田", region: "nt",
    lat: 22.3825, lng: 114.1880, category: "park", indoor: false,
    ageRange: [0, 12], priceType: "free", priceDescription: "免費",
    description: "史努比主題公園，6個遊樂區",
    website: "https://www.shatin.mk", tips: "新城市廣場3樓平台",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: false,
    openingHours: "11:00-19:00", address: "沙田正街18號新城市廣場"
  },
  {
    id: "020", name: "青衣公園", district: "青衣", region: "nt",
    lat: 22.3540, lng: 114.1020, category: "park", indoor: false,
    ageRange: [0, 12], priceType: "free", priceDescription: "免費",
    description: "大型公園，有恐龍主題遊樂場、腳船",
    website: "https://www.lcsd.gov.hk", tips: "恐龍設施很吸引",
    hasBabyRoom: true, hasStrollerAccess: true, hasRestaurant: true, rainyDaySuitable: false,
    openingHours: "24小時", address: "青衣青綠街"
  },
  // 繼續添加至50個...
];

export default locations;
