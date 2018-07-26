#List of libraries needed, will automatically install if not present
try:
    import requests
except:
    import pip
    pip.main(['install', 'requests'])
    import requests

try:
    import pandas as pd
except:
    import pip
    pip.main(['install', 'pandas'])
    import pandas as pd

try:
    import json
except:
    import pip
    pip.main(['install', 'json'])
    import json

#Ensure Canvas API token is in the designated file Canvas API Token.txt
print ('Before you begin the process, please ensure you have copy & pasted your Canvas API token into the file Canvas API Token.txt.')
confirmation = input ('Input any key to continue:')

with open('Canvas API Token.txt','r') as f:
    for line in f:
        for word in line.split():
           token = word   

#Course url
url = "https://ubc.instructure.com/"

#Course number
course = input('Input course ID and hit ENTER:\n')

#The assignment ID number
assignment_id = input('Assignment ID number and hit ENTER:\n')

print ('Processing data, please wait......\n')

try:
#Obtaining the assignment information (settings, assignment id, rubric id)
    assignmentInfo = requests.get(url + '/api/v1/courses/' + str(course) + '/assignments/' + assignment_id,
                 headers= {'Authorization': 'Bearer ' + token})
#Extracting assignment rubric id/rubric for the assignment
    assignmentInfo = json.loads(assignmentInfo.text)

    rubric_id = str(assignmentInfo['rubric_settings']['id'])

    payload = {'include': 'peer_assessments',
           'style' : 'full'}
    r = requests.get(url + '/api/v1/courses/' + str(course) + '/rubrics/' + rubric_id,
                 params = payload,
                 headers= {'Authorization': 'Bearer ' + token})

    rubric_return = json.loads(r.text)
#Obtaining assessor_id (person who did peer review), score for the peer reviews
    assessments_df = pd.DataFrame(rubric_return['assessments'])

#Obtaining user_id (person who was peer reviewed), completion and submission comments
    peerReview = requests.get(url + '/api/v1/courses/' + str(course) + '/assignments/' + assignment_id + '/peer_reviews',
                 headers= {'Authorization': 'Bearer ' + token})

    peerReviewInfo = json.loads(peerReview.text)
    peerReview_df = pd.read_json(peerReview.text)
    peerReview_df['user_id'] = peerReview_df['user_id'].astype(str)
    
#Merging data together into one csv file named 'peer review information.csv'
    merged_df = pd.merge(peerReview_df, assessments_df, how='outer', left_on=['assessor_id', 'asset_id'], right_on=['assessor_id', 'artifact_id'])
    merged_df.to_csv('peer_review_information.csv')
    print("peer review information file created")

#Counts the number of peer reviews a student has completed, places into list with user_id (accessor_id)
    completed_peer_review_count = {}
    for index, row in merged_df.iterrows():
        assessor_id = str(row['assessor_id'])
        completed_peer_review_count.setdefault(assessor_id, 0)

        if row['workflow_state'] == 'completed':
            completed_peer_review_count[assessor_id] += 1
            peer_review_count = completed_peer_review_count[assessor_id]
            
    
    print('Data successfully gathered.\n')
#if input is True, uploads scores onto Canvas Gradecenter (does not create new assignment)
    upload = input ('Type True to upload peer review scores onto Gradecenter.\n')
    if upload==True:
    
        print("Data Should be Uploaded onto Gradecenter.")
        for assessor_id, peer_review_count in completed_peer_review_count.items():
            grade = 0
            if peer_review_count > 0:
                grade = str(peer_review_count)

                r = requests.put(
                    url + '/api/v1/courses/' + str(course) + '/assignments/'+ str(assignment_id) +'/submissions/' + str(assessor_id) + '/',
                    params={'submission[posted_grade]': grade},
                    headers= {'Authorization': 'Bearer ' + token}
                    )
    else:
        print('Data not uploaded.')
                
except KeyError:
    print ("Something went wrong. Perhaps you provided an invalid...../n")
    print ("Course ID?")
    print ("Canvas API Token?")
    print ("Assignment ID?")
