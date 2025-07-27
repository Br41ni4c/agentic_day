from google.adk.agents import Agent, ParallelAgent, SequentialAgent

# from toolbox_core import ToolboxClient
from .mongo_personal_probability_tool import calculate_user_location_probability

firebase_reader_agent = Agent(
    name="firestore_reader_agent",
    model="gemini-2.5-pro",
    description="An agent that can read from a firestore database",
    instruction="""
    You are the absolute master at reading data from a firestore database.
    You will use whatever tool is available at your disposal to query the
    necessary documents off a firestore mongodb collection.
    """,
)

personal_probability_agent = Agent(
    name="personal_probaility_agent",
    model="gemini-2.5-pro",
    description="""
    Accept the location and time of a potential expense entry and
    compute the probability of a legit purchase for the potential 
    expense entry.
    """,
    instruction="""
    I will accept a bunch of expense record entries from a relevant
    time frame and the current potential entry's location and time
    and use the various parameters such as the time of day and any
    other relevant information to calculate the probaility of that
    being a legitimate expense entry.
    I will accept the (user_name) and (location) as inputs and find the
    correponding probability. For now I will use "siva" for name and "dmart, hsr" for location and I will
    not prompt user for input.
    You will return the probability and the list of entries you
    considered to arrive at this result.
    """,
    tools=[calculate_user_location_probability],
)

public_probability_agent = Agent(
    name="public_probability_agent",
    model="gemini-2.5-pro",
    description="""
    Accepts the location and tries to find similar user as a class
    and generate a probability by checking if they have purchase
    activity in the vicinity.
    """,
    instruction="""
    I will take the location and user name as the input and then
    query a set of expense records in a given radius of the location
    (100m is the default). We will then identify the users who made
    these purchases and calculate a probability based on these users
    and our target user based on how alike they are using a set of
    criteria like age, gender, address, etc., 
    I will finally return the probability value and the list of users
    i took into consideration.
    """,
    sub_agents=[firebase_reader_agent],
)

calculator_agent = ParallelAgent(
    name="purchase_probability_calculator_agent",
    description="""
    Agent to determine probability of a purchase based on location parameters
    from previous spending patterns of the user and other users from the user's class.
    """,
    sub_agents=[personal_probability_agent, public_probability_agent],
)

decision_agent = Agent(
    name="decsion_agent",
    description="""
    Accepts the respective probabilities from the previous agents
    and decides on an appropriate weight based on user data and class
    composition to decide if the location suggests that some purchase
    has been made in the given location and yields the result.
    """,
    instruction="""
    I am an expert data analyst who's capable of determining the
    correlation between numerous data points and figuring out the likeliness
    based on similarity of attributes.
    1. I will get the data points used and the probability value calculated
    fomr the personal_probaility_agent and compare it to observe spending
    trends like time of day and other attributes which you deem appropriate
    to offers decent level inference from the presented information to set
    a weight for that probability.
    
    2. I will also get the user id list used by the public_probaility_agent
    and try to establish a measure of similarity or some measure to determine
    whether the selected user's behaviour is reasonable consideration to determine
    the target user's spending pattern and generate a proper weight for this\
    probability as will.

    3. I will finally aggregate these probabilities to arrive at a result,
    determine a threshold above which this qualifies as a potential purchase
    by the target user, decide if the result crosses the threshold and then
    say yes or no.
    """,
    model="gemini-2.5-pro",
)

aggregator_agent = SequentialAgent(
    name="purchase_probability_aggregator_agent",
    description="""
    Agent to determine probability of a purchase based on location parameters
    by aggregating the results from the sub agents.
    """,
    sub_agents=[calculator_agent, decision_agent],
)

root_agent = aggregator_agent
