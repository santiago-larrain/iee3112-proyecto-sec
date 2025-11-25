import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import CasoDetalle from '../views/CasoDetalle.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/caso/:id',
    name: 'CasoDetalle',
    component: CasoDetalle,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

