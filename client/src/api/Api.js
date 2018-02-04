import axios from 'axios'

export default {
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
  login (username, password) {
    return new Promise(function (resolve, reject) {
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
  }
}
