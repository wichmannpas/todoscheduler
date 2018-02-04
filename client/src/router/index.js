import Vue from 'vue'
import VueRouter from 'vue-router'

import LoginPage from '@/pages/LoginPage'
import OverviewPage from '@/pages/OverviewPage'

Vue.use(VueRouter)

export default new VueRouter({
  routes: [
    {
      path: '/',
      name: 'overview',
      component: OverviewPage
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage
    }
  ]
})
