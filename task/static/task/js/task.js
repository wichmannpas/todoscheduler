(function () {
  /**
   * Close all modals.
   */
  function closeModals() {
    $('.modal').removeClass('active');
  }

  /**
   * Initialize and display the new task modal.
   */
  function initNewTask(event) {
    if (event !== undefined) {
      event.preventDefault();
    }
    let name = $('#new_task_name');
    name.val('');
    $('#new_task_duration').val(1);
    $('#new_task').addClass('active');

    name.focus();
  }

  /**
   * Initialize and display the schedule modal.
   */
  function initSchedule(event) {
    if (event !== undefined) {
      event.preventDefault();
    }
    let task = $(this).parent();
    let durationInput = $('#schedule_duration');

    $('#schedule_data_name').text(task.data('name'));
    $('#schedule_data_unscheduled_duration').text(task.data('unscheduled-duration'));
    $('#schedule_id').val(task.data('taskid'));
    durationInput.val(task.data('unscheduled-duration'));

    $('#schedule').addClass('active');
    $('#schedule_for').val('today');
    $('#schedule_for_date').hide();
    durationInput.focus();
  }

  $(function () {
    $('#new_task_link').click(initNewTask);
    let scheduleFor = $('#schedule_for');
    scheduleFor.change(function () {
      let scheduleForDate = $('#schedule_for_date');
      if (scheduleFor.val() === 'another_time') {
        scheduleForDate.show();
      } else {
        scheduleForDate.hide();
      }
    });
    $('.task-schedule').click(initSchedule);
    $('.modal-close').click(closeModals);
    $('.modal-overlay').click(closeModals);
  });
})();