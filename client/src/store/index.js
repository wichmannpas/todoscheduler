import Vue from 'vue'
import Vuex from 'vuex'

import tasks from './tasks'
import taskexecutions from './taskexecutions'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    tasks,
    taskexecutions
  }
})
