#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 11:26:47 2015

@author: Jimmy Da Silva <jimmy.dasilva@isir.upmc.fr>
"""
from depth_cam_tools.kinect import Kinect
import rospy
import cv2
import tf
import sys
import numpy as np
from threading import Thread
from scipy import stats
from ar_track_alvar_msgs.msg import AlvarMarkers

class TrackingGui(Thread):
    def __init__(self,sensor_type, sensor_name):
        Thread.__init__(self)
        if sensor_name[-1] == '/':
            sensor_name = sensor_name[:-1]
        
        if (sensor_type == "Kinect2") or (sensor_type == "Kinectv2") or (sensor_type == "Kinect_v2"):
            print "Loading "+sensor_name+" of type Kinect2"
            print "ERROR: Kinect2 offset is already been computed during the intrinsics calibration. Nothing to be done here"
            return
        elif (sensor_type == "Kinect") or (sensor_type == "Kinect1") or (sensor_type == "Kinectv1") or (sensor_type == "Kinect_v1"):
            print "Loading "+sensor_name+" of type Kinect1"
            self.kinect = Kinect(sensor_name,queue_size=10,compression=False,use_rect=True,use_depth_registered=True,use_ir=False)
        else:
            print "ERROR: Sensor type must be Kinect2 or Kinect"
            return       
        
        self.sensor_name = sensor_name
        self.kinect.wait_until_ready()
        
        self.list_robot_links = ['link_1','link_2','link_3','link_4','link_5','link_6','link_7']
        
        rospy.Subscriber("/ar_pose_marker", AlvarMarkers , self.callback)

    def start(self):
        
        listener = tf.TransformListener()        
        
        while not rospy.is_shutdown():
            depth_img = self.kinect.get_depth(blocking=False)
            img_height, img_width = depth_img.shape[:2]
            depth_array = np.array(depth_img, dtype=np.float32)
            
            cv2.normalize(depth_array, depth_array, 0, 1, cv2.NORM_MINMAX)
            
            depth_8u = depth_array*255
            depth_8u = depth_8u.astype(np.uint8)          
            
            depth_color = cv2.cvtColor(depth_8u ,cv2.COLOR_GRAY2RGB)            
              
             
            lst_pixels = [None] * len(self.list_robot_links)
            for i in range(len(self.list_robot_links)):
                try:
                    (trans,_) = listener.lookupTransform(self.kinect.rgb_optical_frame,self.list_robot_links[i], rospy.Time(0))
                    pixels = self.kinect.world_to_depth(trans,use_distortion=True)
                    if (pixels[0]<0) or (pixels[1]<0) or (pixels[0]>img_width) or (pixels[1]>img_height):
                        continue
                    cv2.circle(depth_color,(int(pixels[0]),int(pixels[1])),5,(0,255,0),-1)
                    lst_pixels[i] = pixels
                    
                except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                    continue
                
            for i in range(len(self.list_robot_links)-1):
                if (lst_pixels[i] is not None) and (lst_pixels[i+1] is not None):
                    cv2.line(depth_color, (int((lst_pixels[i])[0]) ,int((lst_pixels[i])[1])), (int((lst_pixels[i+1])[0]) ,int((lst_pixels[i+1])[1])), (255,0,0))
            
            cv2.imshow("DETPH_PLUS_PTS", depth_color)
            cv2.waitKey(10)

    def callback(self,data):
        return
                        
def main(argv):
    rospy.init_node("tracking_visu",anonymous=True)
    if rospy.has_param("/use_sim_time"):
        rospy.logwarn("Using simulation time")
        while not rospy.Time.now():
            pass # tsim syncing
       
    sensor_name = rospy.get_param('~sensor_name')
    sensor_type = rospy.get_param('~sensor_type')
    
    gui = TrackingGui(sensor_type, sensor_name)
    gui.start()
    rospy.spin()

if __name__ == '__main__':
    main(sys.argv)
    exit(0)