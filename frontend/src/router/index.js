import { createRouter, createWebHistory } from 'vue-router'
import FavoritesView from '../views/FavoritesView.vue'
import HomeView from '../views/HomeView.vue'
import MapView from '../views/MapView.vue'
import ProfileView from '../views/ProfileView.vue'

const routes = [
  { path: '/', redirect: '/map' },
  { path: '/avatar', name: 'avatar', component: HomeView, meta: { keepAlive: true } },
  { path: '/map', name: 'map', component: MapView },
  { path: '/favorites', name: 'favorites', component: FavoritesView },
  { path: '/profile', name: 'profile', component: ProfileView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
