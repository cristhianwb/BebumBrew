#ifndef USER_TIMER_H
#define USER_TIMER_H


typedef bool (*timer_callback_t) (uint8_t);


/**
 * A User timer to control actions in the main loop of a arduino sketch
 * 
 * 
 * */
class UserTimer {
  public:
    bool* timerStates;

    UserTimer();
  
    void update();

    /*
      The callback should return true if wants to continue to be called, otherwise should return false (if wants to be called once), 
      this is why she returns a bool value
    */

    uint8_t addTimer(int time_millis, bool auto_start, timer_callback_t timer_callback);

    void startTimer(uint8_t timer_index);
    void stopTimer(uint8_t timer_index);
    void setTime(int time_millis, uint8_t timer_index);


  private:
    uint8_t timerCount;
    
    unsigned long* lastMillisArray;
    unsigned long* timerTimes;
    timer_callback_t* callbacks;
  
};

#endif
