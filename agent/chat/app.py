import streamlit as st
import matplotlib.pyplot as plt


# Create a Matplotlib chart
def create_chart():
    plt.figure(figsize=(6, 4))
    plt.plot([1, 2, 3, 4], [10, 20, 25, 30], label="Line 1")
    plt.plot([1, 2, 3, 4], [30, 25, 20, 10], label="Line 2")
    plt.title("Sample Matplotlib Chart")
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.legend()
    plt.grid(True)


# Streamlit app
st.title("Matplotlib Chart in Streamlit")
st.write("Below is a chart rendered using Matplotlib:")

# Generate and display the chart
create_chart()
st.pyplot(plt)
