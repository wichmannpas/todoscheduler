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
          console.error(error)
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
        console.error(error)
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
      store.dispatch('setIncompleteTasks', response.data)
    })
  },
  finishTask (store, task) {
    return new Promise(function (resolve, reject) {
      let duration = task.duration.sub(task.incompleteDuration())
      if (duration.toNumber() <= 0) {
        // unscheduled task, delete it
        axios.delete('/api/tasks/task/' + task.id.toString() + '/').then(function (response) {
          if (response.status === 204) {
            store.commit('deleteIncompleteTask', task)

            resolve()
          } else {
            reject(response.data)
          }
        }).catch(function (error) {
          console.error(error)
          reject(error.response.data)
        })
      } else {
        // update the task duration
        axios.patch('/api/tasks/task/' + task.id.toString() + '/', {
          duration: duration
        }).then(function (response) {
          if (response.status === 200) {
            store.dispatch('updateTask', response.data)
            store.dispatch('updateTaskInExecutions', response.data)
            resolve()
          } else {
            reject(response.data)
          }
        }).catch(function (error) {
          console.error(error)
          reject(error.response.data)
        })
      }
    })
  },
  scheduleTask (store, task, day, duration) {
    return new Promise(function (resolve, reject) {
      axios.post('/api/tasks/taskexecution/', {
        task_id: task.id,
        day: day,
        duration: duration
      }).then(function (response) {
        if (response.status === 201) {
          store.dispatch('updateTask', response.data.task)
          store.dispatch('addTaskExecution', response.data)

          resolve()
        } else {
          reject(response.data)
        }
      }).catch(function (error) {
        console.error(error)
        reject(error.response.data)
      })
    })
  },
  getTaskExecutions (store) {
    axios.get('/api/tasks/taskexecution/').then(function (response) {
      for (let i = 0; i < response.data.length; i++) {
        store.commit('setTaskExecutionsForDay', response.data[i])
      }
    })
  },
  createTask (store, task) {
    return new Promise(function (resolve, reject) {
      axios.post('/api/tasks/task/', {
        name: task.name,
        duration: task.duration,
        start: task.start
      }).then(function (response) {
        if (response.status === 201) {
          store.commit('addIncompleteTask', response.data)
          resolve(response.data)
        } else {
          reject(response.data)
        }
      }).catch(function (error) {
        console.error(error)
        reject(error.response.data)
      })
    })
  },
  updateTask (store, task) {
    return new Promise(function (resolve, reject) {
      axios.put('/api/tasks/task/' + task.id.toString() + '/', {
        name: task.name,
        duration: task.duration,
        start: task.start
      }).then(function (response) {
        if (response.status === 200) {
          store.dispatch('updateTask', response.data)
          store.dispatch('updateTaskInExecutions', response.data)
          resolve()
        } else {
          reject(response.data)
        }
      }).catch(function (error) {
        console.error(error)
        reject(error.response.data)
      })
    })
  },
  changeTaskDuration (store, task, newDuration) {
    return new Promise(function (resolve, reject) {
      axios.patch('/api/tasks/task/' + task.id.toString() + '/', {
        duration: newDuration
      }).then(function (response) {
        store.dispatch('updateTask', response.data)
        store.dispatch('updateTaskInExecutions', response.data)

        resolve()
      })
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
        store.commit('deleteTaskExecution', execution)
        if (postpone) {
          let task = execution.task
          task.scheduledDuration = task.scheduledDuration.sub(execution.duration)
          store.dispatch('updateTask', task)
          store.dispatch('updateTaskInExecutions', task)
        }

        resolve()
      })
    })
  },
  changeTaskExecutionDuration (store, execution, newDuration) {
    return new Promise(function (resolve, reject) {
      axios.patch('/api/tasks/taskexecution/' + execution.id.toString() + '/', {
        duration: newDuration
      }).then(function (response) {
        store.dispatch('updateTaskExecution', response.data)
        store.dispatch('updateTask', response.data.task)
        store.dispatch('updateTaskInExecutions', response.data.task)

        resolve()
      })
    })
  },
  exchangeTaskExecution (store, execution, exchange) {
    return new Promise(function (resolve, reject) {
      axios.patch('/api/tasks/taskexecution/' + execution.id.toString() + '/', {
        day_order: exchange.dayOrder
      }).then(function (response) {
        store.dispatch('updateTaskExecution', response.data)
        exchange.dayOrder = execution.dayOrder
        store.dispatch('updateTaskExecution', exchange)

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
        store.dispatch('updateTask', response.data.task)
        store.dispatch('updateTaskInExecutions', response.data.task)

        resolve()
      })
    })
  },
  updateTaskExecutionDay (store, execution, newDay) {
    return new Promise(function (resolve, reject) {
      axios.patch('/api/tasks/taskexecution/' + execution.id.toString() + '/', {
        day: newDay
      }).then(function (response) {
        store.dispatch('updateTaskExecution', response.data)

        resolve()
      })
    })
  }
}
