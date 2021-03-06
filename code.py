import sys
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os

def main():
	# Define Video Writer object
	cap = cv2.VideoWriter('Data1.mp4',cv2.VideoWriter_fourcc(*'MP4V'), 20.0, (1280,370))
	
	# Define Path of the Dataset
	path = './Dataset/data_1/data/'

	# Get frames in order
	imgs = sorted(os.listdir(path))
 
	for i in imgs:
		
		# Read Image
		img = cv2.imread(path + str(i))
		print(path + str(i))
		h,  w = img.shape[:2]
		
		# Given camera instrinsic parameters
		K = np.array([[9.037596e+02, 0.000000e+00, 6.957519e+02],
						[0.000000e+00, 9.019653e+02, 2.242509e+02],
						 [0.000000e+00, 0.000000e+00, 1.000000e+00]])
		
		# Given camera distortion parameters
		dist = np.array([ -3.639558e-01 ,1.788651e-01, 6.029694e-04 ,-3.922424e-04 ,-5.382460e-02])
		newcameramtx, roi = cv2.getOptimalNewCameraMatrix(K, dist, (w,h), 1, (w,h))

		#Undistorted Image
		dst = cv2.undistort(img,K,dist,None,newcameramtx)
		
		# 4 points for Homography image and ground truth
		h_pts_img = np.array([[364,417],[643,240],[700,240],[846,417]], dtype="float32")
		h_pts_gt = np.array([[32,512],[32,0],[192,0],[192,512]],dtype="float32")
		H,_ = cv2.findHomography(h_pts_img, h_pts_gt)

		# Birds Eye View		
		warped = cv2.warpPerspective(dst,H,(256,512))
		gray = cv2.cvtColor(warped,cv2.COLOR_BGR2GRAY)
		
		# Threshold the lanes
		edges = np.zeros((gray.shape[0],gray.shape[1]),dtype=np.uint8)
		edges[gray>245] = 255

		# Plot Histograms for left half and right half
		hist_along_x_left = np.sum(edges[:,:int(edges.shape[1]/2)]>0, axis=0)
		hist_along_x_right = np.sum(edges[:,int(edges.shape[1]/2):]>0, axis=0)

		##  Uncomment for histogram plot
		# plt.figure("Threshold")
		# plt.imshow(edges,cmap="gray")
		# plt.plot(hist_along_x_left)
		# plt.plot(np.hstack([np.zeros_like(hist_along_x_left), hist_along_x_right]))
		# plt.show()

		# Extract the peaks
		left_lane = np.argmax(hist_along_x_left)
		right_lane = int(edges.shape[1]/2) + np.argmax(hist_along_x_right)

		# Remove surrounding noisy predictions
		if left_lane-15>0:
			edges[:, :left_lane-15] = 0
		edges[:, left_lane+15:int(edges.shape[1]/2)]=0
		edges[:, int(edges.shape[1]/2):right_lane-15]=0
		if right_lane+15<edges.shape[0]:
			edges[:, right_lane+15:]=0

		# Left and Right Lane feature extraction	
		left_lane_pts = np.where(edges[:, :left_lane+15]>0)
		right_lane_pts = np.where(edges[:, right_lane-15:]>0)
		right_lane_pts = (right_lane_pts[0], (right_lane -15 + right_lane_pts[1]))

		# Find the best fit equation for left and right lanes
		pl = np.polyfit(left_lane_pts[0],left_lane_pts[1],2)
		pr = np.polyfit(right_lane_pts[0],right_lane_pts[1],2)
		
		# Radius of curvature formula https://www.quora.com/How-can-I-find-the-curvature-of-parabola-y-ax-2-bx-c
		curvature =(10**11) * ((2*pr[0])/((1+((2*pr[0]*(-pr[2]/(2*pr[0])))+pr[1])**2)*np.sqrt(1+((2*pr[0]*(-pr[2]/(2*pr[0])))+pr[1])**2)))
		
		# Curvature heuristic
		curve = "Straight"
		if (curvature>(0.8)):
			curve = "Right"
		if (curvature<-0.7):
			curve = "Left"		

		# Get lane points accross polyfit equations
		lane = np.zeros((warped.shape[0],warped.shape[1],2))
		for x in range(0,512):
			if (((pl[0]*(x**2)) + (pl[1]*(x**1)) + (pl[2])) < 256) and (((pl[0]*(x**2)) + (pl[1]*(x**1)) + (pl[2])) > 0):
				lane[x,int((pl[0]*(x**2)) + (pl[1]*(x**1)) + (pl[2])),0] = 255
			lane[x,int((pr[0]*(x**2)) + (pr[1]*(x**1)) + (pr[2])),1] = 255

		# Inverse Perspective Transform onto camera frame
		world_lane_left = cv2.warpPerspective(lane[:,:,0],np.linalg.inv(H),(w,h))
		world_lane_right = cv2.warpPerspective(lane[:,:,1],np.linalg.inv(H),(w,h))

		dst[world_lane_left>0] = [255,0,0]
		dst[world_lane_right>0] = [0,0,255]

		# Get points for FillPoly the lane 
		left = np.argwhere(world_lane_left>0)
		left = np.flip(left,axis=1)
		right = np.argwhere(world_lane_right>0)
		right = np.flip(right,axis=1)

		poly_lane = np.zeros((dst.shape[0],dst.shape[1],3),np.uint8 )
		poly_lane = cv2.fillPoly(poly_lane,[np.vstack((np.flip(left,axis=0),right))],[0,255,0])

		# Add Lane onto the Undistorted Image
		dst = cv2.addWeighted(dst,0.8,poly_lane,0.2,1)
		dst = cv2.putText(dst,curve,(500,150),1,cv2.FONT_HERSHEY_DUPLEX,(0,0,255),2,cv2.LINE_AA)
		cv2.imshow("Lane World",dst[60:430,50:1330])
		cap.write(dst[60:430,50:1330])
		cv2.waitKey(1)
	print("Saving Video!")
	cap.release()


if __name__=="__main__":
	main()
