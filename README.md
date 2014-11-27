this is a  server using flask
to run simply do:  
   pip install flask
   python masterapp_flask.py 


you can test with curl thus:
curl -F query="hiii this is a test" -F query_file=@"bc-30-sc-correct-20141022/bc-30-sc-correct-20141022/55/155c_A.pds" http://localhost:5000/api/search
