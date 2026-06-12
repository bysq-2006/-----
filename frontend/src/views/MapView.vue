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
