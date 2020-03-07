var counters = [];

function Counter(name, seconds, display, endContent, onFinished, onFinishedTitle=null, onFinishedIcon=null){
	this.name = name;
	this.started = new Date().getTime();
	this.endTime = new Date().getTime() + seconds*1000;
	this.display = display;
	this.endContent = endContent;
	this.onFinished = onFinished;
	this.onFinishedTitle = onFinishedTitle;
	this.onFinishedIcon = onFinishedIcon;

	// return remaining time in seconds
	this.remainingTime = function(){ return Math.ceil((this.endTime - new Date().getTime())/1000); };

	var even = false;
	// update counter
	this.update = function(){
		// init the object, return false if could not find the element after 20 seconds
		if(!this.obj) this.obj = document.getElementById(this.name);
		if(!this.obj && new Date().getTime() - this.started > 20000) return false;
		if(!this.obj) return true;

		try{
			var s = this.remainingTime();
			var s2 = this.endTime;

			if(s <= 0){
				if(this.endContent != '')
					this.obj.innerHTML = this.endContent;
				else{
					//if(even)
						this.obj.innerHTML = formatRemainingTime(0);
					//else
					//	this.obj.innerHTML = new Date(s2).toLocaleString('fr-FR', { timeZone: 'Europe/Paris' });
					even = !even;
				}

				if(this.onFinishedTitle){
					if(this.onFinishedIcon){
						notify(this.onFinishedTitle,this.onFinishedIcon);
					}else{
						notify(this.onFinishedTitle);
					}
				}

				if(this.onFinished){
					//this.onFinished(this);
					this.onFinished = null;
				}

				return false;
			} else
			if(s > 0 && (this.display == null) && timers_enabled){
					//if(even)
						this.obj.innerHTML = formatRemainingTime(s);
					//else
					//	this.obj.innerHTML = new Date(s2).toLocaleString('fr-FR', { timeZone: 'Europe/Paris' });
					even = !even;
			}
			return true;
		}catch(e){
			return false;
		}
	};

	this.toString = function(){
		var s = this.remainingTime();
		var s2 = this.endTime;
		var toDisplay = this.display;
		if(!toDisplay) toDisplay = (s<=0 && this.endContent != '')?this.endContent:formatRemainingTime(s);
		return '<span id="' + this.name + '">' + toDisplay + '</span>';
	};
}

function startCountdown(name, seconds, displayCountdown, endContent, onFinished, onFinishedTitle=null,onFinishedIcon=null){
	var c = new Counter(name, seconds, displayCountdown, endContent, onFinished, onFinishedTitle, onFinishedIcon);
	counters.push(c);
	return c;
}

function updateCounters(){
	for(var x in counters){
		if(counters[x] != null)
			if(!counters[x].update()) counters[x] = null;
	}

	window.setTimeout("updateCounters()", 1000);
}

updateCounters();


function formattime(s){
	d=Math.floor(s/(3600*24));

	h=Math.floor(s/3600)%24;
	if(h<10){h="0"+h;}

	m=Math.floor(s/60)%60;
	if(m<10){m="0"+m;}

	s=s%60;
	if(s<10){s="0"+s;}

	if (d > 0)
		return d + dayletter + " " + h + ":" + m + ":" + s;
	else
		return h + ":" + m + ":" + s;
}

function formatRemainingTime(s){
	if(s < 0) s = 0;
	if(s < 600) return "<span id=countdown>" + formattime(s) + "</span>";
	return formattime(s);
}

var countdownnbr = 0;

function putcountdown1(seconds, endlabel, url, text=null, icon=null)
{
	var c = startCountdown('cntdwn' + countdownnbr++, seconds, null, '<a href="' + url + '">' + endlabel + '</a>', null, text, icon);
	document.write(c);
}

function putcountdown2(seconds, content1, content2, text=null, icon=null)
{
	var c = startCountdown('cntdwn' + countdownnbr++, seconds, content1, content2, null, text, icon);
	document.write(c);
}
