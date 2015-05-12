/* --------------------------------------------------------------------------
 * SpeechBuddy Body Detection
 * --------------------------------------------------------------------------
 * author: Erica Du
 * date:  4/2015 (m/y)
 * ----------------------------------------------------------------------------
 */

import SimpleOpenNI.*;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.io.IOException;
import processing.video.*;


// Kinect Library object
SimpleOpenNI context;
PVector com = new PVector();
PVector com2d = new PVector();
Table positions;
boolean start = false;
String[] skeletonNames = { "head", "neck", "leftshoulder", "leftelbow", "lefthand", "rightshoulder", "rightelbow", "righthand", "torso", "lefthip", "leftknee", "leftfoot", "righthip", "rightknee", "rightfoot" };
HashMap<String, Integer> skeleton = new HashMap<String, Integer>();
int[] skeletonIds;
boolean hastracked = false;
PrintWriter output;
String[] cameras = Capture.list();
Capture cam;

void setup()
{
  size(640,480);
  frameRate(25);
  
  context = new SimpleOpenNI(this);
  if(context.isInit() == false)
  {
     println("Can't init SimpleOpenNI, maybe the camera is not connected!"); 
     exit();
     return;  
  }
  
  // enable depthMap generation 
  context.enableDepth();
  context.enableRGB();
  
  // enable skeleton generation for all joints
  context.enableUser();
  
  stroke(0,0,255);
  strokeWeight(3);
  smooth(); 
  
  setupTable();
  
  // Draw Welcome Message
  textSize(32); // Set text size to 32
  fill(0);
  text("Welcome to SpeechBuddy!", 100, 100);
  textSize(17);
  text("Wait for the red circle to disappear to start your presentation.", 70, 180);
  text("Please press the space bar when you are done.", 100, 210);
  textSize(24); // Set text size to 32
  text("Click anywhere to begin.", 150, 270);
  getSkeletonList();
  
  if (cameras.length == 0) {
    println("There are no cameras available for capture.");
    exit();
  } else {
    println("Available cameras:");
    for (int i = 0; i < cameras.length; i++) {
      println(cameras[i]);
    }
    
    // The camera can be initialized directly using an 
    // element from the array returned by list():
    cam = new Capture(this, cameras[0]);
    cam.start();     
  } 
}

void draw()
{
  saveFrame("data/images/speech-#####.tif");
  if (start) {
    // update cam
    context.update();
    image(context.userImage(),0,0);
    
    // Affordance for UI to tell user when to start presenting
    if (!hastracked)
    {
      // Draw red circle
      fill(255,0,0);
      ellipse(100,100,100,100);
    }
    
    // get joint position of user
    int[] userList = context.getUsers();
    for (int i=0; i<userList.length; i++)
    {
      if (context.isTrackingSkeleton(userList[i]))
      {
        // Create new row for table
        TableRow newRow = positions.addRow();
        newRow.setInt("user", userList[i]);
        newRow.setInt("timestamp", millis());
        hastracked = true;
        set(0, 0, cam);
        println("nowtracking");
        
        for (int j=0; j<skeletonNames.length; j++)
        {
          PVector jointPos = new PVector();
          context.getJointPositionSkeleton(userList[i],skeleton.get(skeletonNames[j]), jointPos);
          String x = skeletonNames[j] + "x";
          String y = skeletonNames[j] + "y";
          String z = skeletonNames[j] + "z";
          println(x, y, z, jointPos.x, jointPos.y, jointPos.z);
          newRow.setFloat(x, jointPos.x);
          newRow.setFloat(y, jointPos.y);
          newRow.setFloat(z, jointPos.z);
          
          if (context.getCoM(userList[i], com))
          {
            newRow.setFloat("comx", com.x);
            newRow.setFloat("comy", com.y);
            newRow.setFloat("comz", com.z);
          } 
        }
        
        if (cam.available() == true) {
          cam.read();
        }
      }
    }
  }
}

// Setup Necessary Data Structures
void getSkeletonList()
{ 
  int[] kinectIds = {SimpleOpenNI.SKEL_HEAD, SimpleOpenNI.SKEL_NECK, SimpleOpenNI.SKEL_LEFT_SHOULDER,
  SimpleOpenNI.SKEL_LEFT_ELBOW, SimpleOpenNI.SKEL_LEFT_HAND, SimpleOpenNI.SKEL_RIGHT_SHOULDER,
  SimpleOpenNI.SKEL_RIGHT_ELBOW, SimpleOpenNI.SKEL_RIGHT_HAND, SimpleOpenNI.SKEL_TORSO,
  SimpleOpenNI.SKEL_LEFT_HIP, SimpleOpenNI.SKEL_LEFT_KNEE, SimpleOpenNI.SKEL_LEFT_FOOT,
  SimpleOpenNI.SKEL_RIGHT_HIP, SimpleOpenNI.SKEL_RIGHT_KNEE, SimpleOpenNI.SKEL_RIGHT_FOOT};
  skeletonIds = kinectIds.clone();
  for (int i=0; i<skeletonNames.length; i++)
  {
    skeleton.put(skeletonNames[i], skeletonIds[i]);
  } 
}

void setupTable()
{
  positions = new Table();
  positions.addColumn("user");
  positions.addColumn("timestamp");
  positions.addColumn("comx");
  positions.addColumn("comy");
  positions.addColumn("comz");
  
  for (int i=0; i<skeletonNames.length; i++)
  {
    positions.addColumn(skeletonNames[i] + "x");
    positions.addColumn(skeletonNames[i] + "y");
    positions.addColumn(skeletonNames[i] + "z");
  }
}

// -----------------------------------------------------------------
// SimpleOpenNI events
void onNewUser(SimpleOpenNI curContext, int userId)
{
  println("onNewUser - userId: " + userId);
  println("\tstart tracking skeleton");
  
  curContext.startTrackingSkeleton(userId);
}

void onLostUser(SimpleOpenNI curContext, int userId)
{
  println("onLostUser - userId: " + userId);
}

void onVisibleUser(SimpleOpenNI curContext, int userId)
{
  //println("onVisibleUser - userId: " + userId);
}

void keyPressed()
{
  switch(key)
  {
  case ' ':
    saveTable(positions, "data/positions.csv");
    cam.stop();
    noLoop();
    exit();
  }
}

void mouseClicked() {
  if (!start) {
    start = true;
    background(0);
  }
}

