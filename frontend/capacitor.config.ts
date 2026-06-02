import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.petmemoji.app",
  appName: "PetMe-Moji",
  webDir: "out",                 // next export 출력 폴더
  bundledWebRuntime: false,
  server: {
    // 프로덕션: 배포된 백엔드 URL 사용. 개발: localhost
    // (NEXT_PUBLIC_API_BASE 환경변수로 프론트엔드가 백엔드를 가리키게 함)
    androidScheme: "https",
    cleartext: false,
  },
  android: {
    backgroundColor: "#fafafa",
    allowMixedContent: false,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1500,
      backgroundColor: "#fce7f3",
      androidSplashResourceName: "splash",
      showSpinner: false,
    },
    StatusBar: {
      style: "DEFAULT",
      backgroundColor: "#ec4899",
    },
  },
};

export default config;
