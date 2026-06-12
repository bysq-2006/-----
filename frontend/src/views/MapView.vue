<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

const mapEl = ref(null)
const AMAP_KEY = import.meta.env.VITE_AMAP_KEY
const CENTER = [120.096477, 31.430194]

let mapInstance = null

async function initMap() {
  if (!AMAP_KEY || !mapEl.value) return
  if (!window.AMapLoader) return

  await nextTick()
  const AMap = await window.AMapLoader.load({
    key: AMAP_KEY,
    version: '2.0',
  })

  mapInstance = new AMap.Map(mapEl.value, {
    center: CENTER,
    zoom: 15,
    viewMode: '2D',
    resizeEnable: true,
  })

  mapInstance.add(
    new AMap.Marker({
      position: CENTER,
      title: '灵山胜境 - 灵山大佛',
    })
  )

  const regionPath = [
    [120.0949, 31.4311],
    [120.0962, 31.4320],
    [120.0981, 31.4314],
    [120.0983, 31.4302],
    [120.0970, 31.4294],
    [120.0957, 31.4298],
  ]

  const region = new AMap.Polygon({
    path: regionPath,
    strokeColor: '#2d8762',
    strokeWeight: 3,
    fillColor: '#2d8762',
    fillOpacity: 0.18,
  })

  const infoWindow = new AMap.InfoWindow({
    content: '<div style="padding:8px 10px;">这是一个示例不规则区域</div>',
    offset: new AMap.Pixel(0, -24),
  })

  region.on('click', (e) => {
    infoWindow.open(mapInstance, e.lnglat)
  })

  mapInstance.add(region)
}

onMounted(initMap)

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.destroy()
    mapInstance = null
  }
})
</script>

<template>
  <div ref="mapEl" class="map-page"></div>
</template>

<style scoped>
.map-page {
  width: 100%;
  height: calc(100vh - 72px);
  min-height: calc(100vh - 72px);
  background: #09130f;
}
</style>
