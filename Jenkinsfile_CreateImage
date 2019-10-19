node {
   stage('Install Python Dependencies') {
      sh '''
        cd AWS/RANDOM
        pip install -r requirements.txt 
      '''
   }
   stage('Run Python Script') {
       sh '''
        cd AWS/RANDOM
        python Create_Image.py --instance_name="$INSTANCE_NAME"
       '''
   }
}
