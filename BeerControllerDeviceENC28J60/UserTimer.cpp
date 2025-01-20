/** @file

 */

#include "Arduino.h"
#include "UserTimer.h"


// Constructor
UserTimer::UserTimer():
  timerCount(0),
  timerStates(NULL),
  lastMillisArray(NULL),
  timerTimes(0),
  callbacks(NULL)
{

}

uint8_t UserTimer::addTimer(int time_millis, bool auto_start, timer_callback_t timer_callback){
  timerCount++;
  timerStates = (bool*) realloc(timerStates, timerCount * sizeof(bool));
  lastMillisArray = (unsigned long*) realloc(lastMillisArray, timerCount * sizeof(unsigned long));
  timerTimes = (unsigned long*) realloc(timerTimes, timerCount * sizeof(unsigned long));
  callbacks = (timer_callback_t*) realloc(callbacks, timerCount * sizeof(timer_callback_t));

  uint8_t timer_index = timerCount-1;

  timerStates[timer_index] = auto_start;
  callbacks[timer_index] = timer_callback;
  timerTimes[timer_index] = time_millis;
  lastMillisArray[timer_index] = millis();
  return timer_index;
}


void UserTimer::startTimer(uint8_t timer_index){
  if (timer_index < timerCount){
    timerStates[timer_index] = true;
  }
}

void UserTimer::stopTimer(uint8_t timer_index){

}

void UserTimer::update(){
  unsigned long current_millis;

  //Serial.println("Timer updated");

  for (uint8_t i = 0;i < timerCount; i++){
    current_millis =  millis();
    //Serial.println(timerTimes[i]);
    if (timerStates[i] && ((current_millis - lastMillisArray[i]) >= timerTimes[i])){
      lastMillisArray[i] = current_millis;
      //Call the callback and update the timer state with the result of the callback 
      timerStates[i] = callbacks[i](i);
    }
  }

}