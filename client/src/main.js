import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './App'
import router from './router'

Vue.use(VueRouter)

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  render: h => h(App)
})
