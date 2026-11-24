<template>
  <svg class="water-cycle-bg" viewBox="0 0 1200 830" preserveAspectRatio="none" aria-hidden="true">
    <defs>
      <linearGradient id="paper" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#F7FBFF" />
        <stop offset="1" stop-color="#EEF6FF" />
      </linearGradient>
      <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
        <path d="M28 0H0V28" fill="none" stroke="#D9E9F7" stroke-width="0.7" />
      </pattern>
      <linearGradient id="river" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#E2F1FF" />
        <stop offset="1" stop-color="#D3EAFF" />
      </linearGradient>
    </defs>

    <rect width="1200" height="830" fill="url(#paper)" />
    <rect width="1200" height="830" fill="url(#grid)" opacity="0.55" />

    <!-- 河流 -->
    <path d="M0 690 C 180 660, 260 760, 430 730 S 760 790, 980 740 S 1140 700, 1200 720 L1200 830 L0 830 Z" fill="url(#river)" />
    <path d="M0 690 C 180 660, 260 760, 430 730 S 760 790, 980 740 S 1140 700, 1200 720" fill="none" stroke="#A9CDEA" stroke-width="1.4" />
    <path d="M0 712 C 180 684, 260 782, 430 752 S 760 812, 980 762 S 1140 722, 1200 742" fill="none" stroke="#C4DEF3" stroke-width="1.1" />
    <path d="M0 734 C 180 708, 260 802, 430 772 S 760 830, 980 784 S 1140 744, 1200 764" fill="none" stroke="#D4E8F8" stroke-width="1" />

    <!-- 水源 / 水库 -->
    <g>
      <rect x="58" y="64" width="196" height="150" rx="16" fill="#E7F3FE" stroke="#A9CDEA" stroke-width="1.6" />
      <path d="M74 118 H238 M74 142 H238 M74 166 H238" stroke="#BBD9F0" stroke-width="1.2" stroke-dasharray="6 7" />
      <path d="M128 64 V214 M182 64 V214" stroke="#C7E0F4" stroke-width="1" />
      <text x="156" y="240" text-anchor="middle" fill="#7FA3C4" font-size="13">水源 / 水库</text>
    </g>

    <!-- 水厂 -->
    <g>
      <rect x="292" y="86" width="122" height="72" rx="8" fill="#F2FAFF" stroke="#A9CDEA" stroke-width="1.5" />
      <path d="M292 106 H414 M316 106 V158 M342 106 V158" stroke="#C7E0F4" stroke-width="1" />
      <circle cx="330" cy="186" r="20" fill="#E7F3FE" stroke="#A9CDEA" stroke-width="1.5" />
      <circle cx="382" cy="186" r="20" fill="#E7F3FE" stroke="#A9CDEA" stroke-width="1.5" />
      <circle cx="434" cy="186" r="20" fill="#E7F3FE" stroke="#A9CDEA" stroke-width="1.5" />
      <g fill="#7FB6E8">
        <circle cx="330" cy="186" r="6" />
        <circle cx="382" cy="186" r="6" />
        <circle cx="434" cy="186" r="6" />
      </g>
      <text x="382" y="238" text-anchor="middle" fill="#7FA3C4" font-size="13">水厂 · 制水</text>
    </g>

    <!-- 主干管 + 加压泵站 -->
    <g fill="none" stroke="#9CC4E8" stroke-width="2.4">
      <path d="M434 214 V262 H640 V316" />
      <path d="M640 262 H760 V300" />
      <path d="M640 262 V420" stroke-dasharray="8 9" />
      <path d="M760 300 H880" stroke-dasharray="8 9" />
    </g>
    <g fill="#BFDCF3">
      <circle cx="434" cy="262" r="5" />
      <circle cx="640" cy="262" r="5" />
      <circle cx="760" cy="300" r="5" />
      <circle cx="520" cy="262" r="4" />
    </g>
    <g transform="translate(494 400)">
      <rect width="72" height="58" rx="8" fill="#F2FAFF" stroke="#A9CDEA" stroke-width="1.5" />
      <circle cx="36" cy="29" r="16" fill="#E7F3FE" stroke="#7FB6E8" stroke-width="1.4" />
      <path d="M30 29 H42 M36 23 V35" stroke="#7FB6E8" stroke-width="1.6" />
      <text x="36" y="84" text-anchor="middle" fill="#7FA3C4" font-size="13">加压泵站</text>
    </g>

    <!-- 城市 / 用户 -->
    <g>
      <rect x="700" y="196" width="58" height="126" rx="4" fill="#F4FAFF" stroke="#A9CDEA" stroke-width="1.4" />
      <rect x="766" y="220" width="46" height="102" rx="4" fill="#F7FCFF" stroke="#A9CDEA" stroke-width="1.4" />
      <rect x="820" y="244" width="52" height="78" rx="4" fill="#F4FAFF" stroke="#A9CDEA" stroke-width="1.4" />
      <rect x="880" y="266" width="38" height="56" rx="4" fill="#F7FCFF" stroke="#A9CDEA" stroke-width="1.4" />
      <g stroke="#C7E0F4" stroke-width="1">
        <path d="M712 216 H746 M712 236 H746 M712 256 H746 M712 276 H746" />
        <path d="M776 240 H802 M776 260 H802 M776 280 H802" />
        <path d="M832 264 H860 M832 284 H860 M832 304 H860" />
      </g>
      <circle cx="744" cy="352" r="10" fill="#E7F3FE" stroke="#A9CDEA" stroke-width="1.2" />
      <path d="M744 352 V340" stroke="#A9CDEA" stroke-width="2" />
      <text x="790" y="386" text-anchor="middle" fill="#7FA3C4" font-size="13">城市 / 用户</text>
    </g>

    <!-- 客服中心 -->
    <g transform="translate(946 232)">
      <rect width="118" height="74" rx="10" fill="#F2FAFF" stroke="#A9CDEA" stroke-width="1.5" />
      <path d="M22 36 a12 12 0 0 1 24 0 v10 h-6 v-10 a6 6 0 0 0 -12 0 v10 h-6 z" fill="#E7F3FE" stroke="#7FB6E8" stroke-width="1.3" />
      <path d="M46 46 h10 M56 46 a12 6 0 0 1 -12 8" fill="none" stroke="#7FB6E8" stroke-width="1.3" />
      <text x="70" y="44" fill="#7FA3C4" font-size="12">服务</text>
      <text x="59" y="96" text-anchor="middle" fill="#7FA3C4" font-size="13">客服中心</text>
    </g>

    <!-- 排水管 -->
    <g fill="none" stroke="#9CC4E8" stroke-width="2.4">
      <path d="M790 344 V470 H780 V520" />
      <path d="M900 344 V470 H900 V520" stroke-dasharray="8 9" />
    </g>

    <!-- 污水厂 -->
    <g>
      <rect x="700" y="524" width="120" height="66" rx="8" fill="#F2FAFF" stroke="#A9CDEA" stroke-width="1.5" />
      <circle cx="860" cy="556" r="26" fill="#E7F3FE" stroke="#A9CDEA" stroke-width="1.6" />
      <circle cx="860" cy="556" r="10" fill="#BFDCF3" />
      <path d="M820 570 H856" stroke="#C7E0F4" stroke-width="1.2" />
      <text x="806" y="622" text-anchor="middle" fill="#7FA3C4" font-size="13">污水厂 · 再生</text>
    </g>

    <!-- 排放口 -->
    <g fill="none" stroke="#9CC4E8" stroke-width="2.2">
      <path d="M900 570 H1010" />
    </g>
    <circle cx="1018" cy="570" r="8" fill="#E7F3FE" stroke="#7FB6E8" stroke-width="1.4" />
    <text x="1046" y="596" text-anchor="middle" fill="#7FA3C4" font-size="13">排放口</text>

    <!-- 监测点 -->
    <g transform="translate(86 552)">
      <path d="M30 0 L58 16 V48 L30 64 L2 48 V16 Z" fill="#E7F3FE" stroke="#A9CDEA" stroke-width="1.5" />
      <path d="M20 32 L28 40 L42 24" fill="none" stroke="#7FB6E8" stroke-width="2" stroke-linecap="round" />
      <text x="30" y="92" text-anchor="middle" fill="#7FA3C4" font-size="13">监测点</text>
    </g>

    <!-- 维护基地 -->
    <g transform="translate(412 560)">
      <path d="M0 30 L36 6 L72 30 V74 H0 Z" fill="#F7FCFF" stroke="#A9CDEA" stroke-width="1.5" />
      <rect x="26" y="46" width="20" height="28" fill="#E7F3FE" stroke="#A9CDEA" stroke-width="1.2" />
      <text x="36" y="100" text-anchor="middle" fill="#7FA3C4" font-size="13">维护基地</text>
    </g>

    <!-- 工程项目 -->
    <g transform="translate(600 560)">
      <path d="M0 78 H90" stroke="#A9CDEA" stroke-width="1.6" />
      <path d="M12 78 V18 H20 V78 Z M20 20 H72 M20 32 H44" stroke="#9CC4E8" stroke-width="1.6" />
      <path d="M72 20 V44" stroke="#7FB6E8" stroke-width="1.4" />
      <rect x="64" y="44" width="16" height="12" fill="#E7F3FE" stroke="#7FB6E8" stroke-width="1.2" />
      <text x="45" y="104" text-anchor="middle" fill="#7FA3C4" font-size="13">工程项目</text>
    </g>

    <!-- 流向箭头 -->
    <g fill="#9CC4E8">
      <path d="M540 256 l10 6 -10 6 z" />
      <path d="M820 294 l10 6 -10 6 z" />
      <path d="M950 564 l10 6 -10 6 z" />
    </g>
  </svg>
</template>

<script setup lang="ts"></script>

<style scoped>
.water-cycle-bg {
  width: 100%;
  height: 100%;
  display: block;
}
</style>
