var calenderView = require('web_calendar.CalendarView');
calenderView.include({
    open_quick_create: function(){
        var calendar_models = ['purchase.order.line'];
        if (!(calendar_models.includes(this.model))) {
            this._super();
        }
    }
 });