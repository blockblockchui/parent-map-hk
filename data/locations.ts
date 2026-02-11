// Sample location data structure
export interface Location {
  id: string;
  name: string;
  nameEn: string;
  category: 'museum' | 'park' | 'playhouse' | 'restaurant' | 'library' | 'shopping';
  district: string;
  region: 'hk-island' | 'kowloon' | 'nt';
  address: string;
  lat: number;
  lng: number;
  ageRange: [number, number];
  indoor: boolean;
  priceType: 'free' | 'low' | 'medium' | 'high';
  hasBabyRoom: boolean;
  hasStrollerAccess: boolean;
  hasRestaurant: boolean;
  rainyDaySuitable: boolean;
  openingHours: string;
  priceDescription: string;
  phone?: string;
  website?: string;
  description: string;
  tips?: string;
  imageUrl?: string;
  affiliateLink?: string;
}

// Sample data - first 10 locations
export const locations: Location[] = [
  {
    id: "001",
    name: "香港科學館",
    nameEn: "Hong Kong Science Museum",
    category: "museum",
    district: "尖沙咀",
    region: "kowloon",
    address: "尖沙咀東部科學館道2號",
    lat: 22.3015,
    lng: 114.1790,
    ageRange: [3, 12],
    indoor: true,
    priceType: "free",
    hasBabyRoom: true,
    hasStrollerAccess: true,
    hasRestaurant: false,
    rainyDaySuitable: true,
    openingHours: "10:00-19:00（周三休館）",
    priceDescription: "免費入場，部分展覽收費",
    phone: "2732 3232",
    website: "https://hk.science.museum",
    description: "互動式科學展覽，小朋友可以動手體驗各種科學原理。有能量傳遞球、鏡子世界等受歡迎展區。",
    tips: "建議平日去，周末人較多。地下有儲物櫃。"
  },
  {
    id: "002",
    name: "香港太空館",
    nameEn: "Hong Kong Space Museum",
    category: "museum",
    district: "尖沙咀",
    region: "kowloon",
    address: "尖沙咀梳士巴利道10號",
    lat: 22.2956,
    lng: 114.1723,
    ageRange: [4, 12],
    indoor: true,
    priceType: "low",
    hasBabyRoom: true,
    hasStrollerAccess: true,
    hasRestaurant: false,
    rainyDaySuitable: true,
    openingHours: "13:00-21:00（周一、三、四、五）\n10:00-21:00（周六、日及公眾假期）\n周二休館",
    priceDescription: "展覽廳：$10，天象廳：$24-$32",
    phone: "2721 0226",
    website: "https://hk.space.museum",
    description: "蛋形建築內有宇宙展覽、天象廳播放星空節目，適合對太空有興趣的小朋友。",
    tips: "天象廳節目要預先買票，建議網上購票。"
  },
  {
    id: "003",
    name: "香港動植物公園",
    nameEn: "Hong Kong Zoological and Botanical Gardens",
    category: "park",
    district: "中環",
    region: "hk-island",
    address: "中環雅賓利道",
    lat: 22.2783,
    lng: 114.1555,
    ageRange: [0, 12],
    indoor: false,
    priceType: "free",
    hasBabyRoom: true,
    hasStrollerAccess: true,
    hasRestaurant: true,
    rainyDaySuitable: false,
    openingHours: "05:00-22:00",
    priceDescription: "免費入場",
    phone: "2530 0154",
    website: "https://www.lcsd.gov.hk/tc/parks/hkzbg/",
    description: "位於中環的綠洲，有紅鸛、狐猴等動物，也有植物溫室。大草坪適合小朋友奔跑。",
    tips: "有斜路推嬰兒車要小心，建議用東華三院入口。"
  },
  {
    id: "004",
    name: "The Big Things Playground",
    nameEn: "The Big Things Playground",
    category: "playhouse",
    district: "荃灣",
    region: "nt",
    address: "荃灣南豐紗廠",
    lat: 22.3756,
    lng: 114.1094,
    ageRange: [0, 8],
    indoor: true,
    priceType: "medium",
    hasBabyRoom: true,
    hasStrollerAccess: true,
    hasRestaurant: true,
    rainyDaySuitable: true,
    openingHours: "10:00-18:00",
    priceDescription: "$160（1大1小），額外成人$50，額外小童$110",
    phone: "3619 0633",
    website: "https://www.thebigthings.com.hk",
    description: "以大自然為主題的室內遊樂場，有木粒沙池、繩網、滑梯等。環境乾淨，職員友善。",
    tips: "記得帶襪，大人細路都要。周末建議預約。"
  },
  {
    id: "005",
    name: "香港濕地公園",
    nameEn: "Hong Kong Wetland Park",
    category: "park",
    district: "天水圍",
    region: "nt",
    address: "天水圍濕地公園路",
    lat: 22.4667,
    lng: 114.0083,
    ageRange: [3, 12],
    indoor: true,
    priceType: "low",
    hasBabyRoom: true,
    hasStrollerAccess: true,
    hasRestaurant: true,
    rainyDaySuitable: true,
    openingHours: "10:00-17:00（周一休館）",
    priceDescription: "$30（成人），$15（小童），周三免費",
    phone: "3152 2666",
    website: "https://www.wetlandpark.gov.hk",
    description: "室內展覽館介紹濕地生態，戶外有觀鳥屋、紅樹林步道。可以近距離觀察雀鳥。",
    tips: "帶望遠鏡觀鳥更佳。室內展館雨天都適合。"
  }
];

// Helper functions
export const getLocationsByRegion = (region: Location['region']) => 
  locations.filter(l => l.region === region);

export const getLocationsByCategory = (category: Location['category']) =>
  locations.filter(l => l.category === category);

export const getLocationsByAge = (age: number) =>
  locations.filter(l => age >= l.ageRange[0] && age <= l.ageRange[1]);

export const getIndoorLocations = () =>
  locations.filter(l => l.indoor);

export const getFreeLocations = () =>
  locations.filter(l => l.priceType === 'free');

export const getRainyDayLocations = () =>
  locations.filter(l => l.rainyDaySuitable || l.indoor);
