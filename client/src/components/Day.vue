<template>
    <div
        class="
          column
          col-3
          col-md-6
          col-sm-12"
        v-bind:class="[
          { 'past-day': day.past() },
          { 'current-day': day.today() },
          { 'overloaded-day': day.overloaded() }
        ]">
      <div class="header">
        {{ day.naturalDay() }}
        <span class="float-right">
        <span class="
          fa fa-clock-o
          tooltip tooltip-left"
              data-tooltip="Max duration for day">
        </span>&nbsp;{{ day.maxDuration().toNumber() }}h
      </span>
      </div>
      <div class="body">
        <TaskExecution
          v-for="execution in day.taskExecutions"
          v-bind:key="execution.id"
          v-bind:execution="execution"/>
      </div>
      <div class="footer">
        <span class="float-right">
          <span class="fa fa-clock-o tooltip"
                data-tooltip="Remaining/total scheduled duration">
          </span>&nbsp;{{ day.remainingDuration().toNumber() }}h/{{ day.scheduledDuration().toNumber() }}h
        </span>
      </div>
    </div>
</template>

<script>
import TaskExecution from '@/components/TaskExecution'

export default {
  name: 'Day',
  props: [
    'day'
  ],
  components: {
    TaskExecution
  }
}
</script>
