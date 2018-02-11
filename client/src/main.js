import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './App'
import router from './router'
import store from './store'

import '@/assets/scss/client.scss'

Vue.use(VueRouter)

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store,
  render: h => h(App)
})
