<template>
  <div class="schedule columns">
    <Day
      v-for="day in days()"
      v-bind:key="day.dayString"
      v-bind:day="day"
    />
  </div>
</template>

<script>
import { addDays, subDays } from 'date-fns'

import Api from '@/api/Api'
import Day from '@/components/Day'

export default {
  name: 'Schedule',
  components: {
    Day
  },
  created: function () {
    Api.getTaskExecutions(this.$store)
  },
  methods: {
    days () {
      let today = new Date()
      let yesterday = subDays(today, 1)
      return this.getListOfDays(yesterday, 8)
    },
    getListOfDays (firstDay, count) {
      let result = []
      let day = firstDay
      for (let i = 0; i < count; i++) {
        result.push(this.$store.getters.taskExecutionsForDay(day))

        day = addDays(day, 1)
      }
      return result
      /*
      return [
        {
          day: 'yesterday',
          past: true,
          today: false,
          overloaded: false,
          executions: [
            {
              id: 42,
              task: {
                id: 42,
                duration: 5,
                name: 'Testtask'
              },
              duration: 2,
              finished: true,
              overdue: false
            },
            {
              id: 42,
              task: {
                id: 42,
                duration: 0.5,
                name: 'Testtask'
              },
              duration: 0.5,
              finished: false,
              overdue: false
            }
          ]
        },
        {
          day: 'today',
          past: false,
          today: true,
          overloaded: false
        },
        {
          day: 'tomorrow',
          past: false,
          today: false,
          overloaded: true
        },
        {
          day: 'todo',
          past: false,
          today: false,
          overloaded: false
        },
        {
          day: 'todo',
          past: false,
          today: false,
          overloaded: false
        },
        {
          day: 'todo',
          past: false,
          today: false,
          overloaded: false
        },
        {
          day: 'todo',
          past: false,
          today: false,
          overloaded: false
        },
        {
          day: 'todo',
          past: false,
          today: false,
          overloaded: false
        }
      ] */
    }
  }
}
</script>
