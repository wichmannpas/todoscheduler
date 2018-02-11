import axios from 'axios'

export default {
  login (username, password) {
    return new Promise(function (resolve, reject) {
      delete axios.defaults.headers.common['Authorization']
      axios.post('/api/token-auth/', {
        username: username,
        password: password
      }).then(
        function (response) {
          let authToken = response.data.token
          window.localStorage.setItem('authToken', authToken)
          resolve()
        }).catch(
        function (error) {
          let response = error.response
          let statusCode
          if (response !== undefined) {
            statusCode = response.status
          }
          if (statusCode === 400) {
            reject(Error('invalid credentials'))
          } else {
            reject(Error('connection error'))
          }
        })
    })
  },
  getAuth () {
    return new Promise(function (resolve, reject) {
      let authToken = window.localStorage.getItem('authToken')
      if (authToken === null) {
        return resolve(false)
      }
      axios.defaults.headers.common['Authorization'] = 'Token ' + authToken

      axios.get('/api/user/').then((response) => {
        return resolve(true)
      }).catch((error) => {
        let response = error.response
        if (response === null) {
          return reject(error)
        }
        return resolve(false)
      })
    })
  },
  getIncompleteTasks (store) {
    axios.get('/api/tasks/task/?incomplete').then(function (response) {
      store.commit('setIncompleteTasks', response.data)
    })
  },
  getTaskExecutions (store) {
    axios.get('/api/tasks/taskexecution/').then(function (response) {
      for (let i = 0; i < response.data.length; i++) {
        store.commit('setTaskExecutionsForDay', response.data[i])
      }
    })
  },
  getMissedTaskExecutions (store) {
    axios.get('/api/tasks/taskexecution/?missed').then(function (response) {
      store.commit('setMissedTaskExecutions', response.data)
    })
  },
  deleteTaskExecution (store, execution, postpone) {
    return new Promise(function (resolve, reject) {
      axios.delete(
        '/api/tasks/taskexecution/' + execution.id.toString() +
        '/?postpone=' + (postpone ? '1' : '0')).then(function (response) {
        store.dispatch('deleteTaskExecution', execution)

        resolve()
      })
    })
  },
  finishTaskExecution (store, execution, newState) {
    return new Promise(function (resolve, reject) {
      axios.patch('/api/tasks/taskexecution/' + execution.id.toString() + '/', {
        finished: newState
      }).then(function (response) {
        store.dispatch('updateTaskExecution', response.data)

        resolve()
      })
    })
  }
}
