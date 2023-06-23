# import matplotlib.pyplot as plt
# import numpy as np

# # Data
# design_to_utilization = {
#     "NO_CFU": {"BRAM": 11.48, "DSP": 1.67, "FF": 2.89, "LUT": 7.15, "LUT_RAM": 0.77},
#     "V4.0": {"BRAM": 11.48, "DSP": 9.58, "FF": 3.08, "LUT": 14.02, "LUT_RAM": 16.94},
#     "V5.0": {"BRAM": 11.48, "DSP": 12.5, "FF": 3.24, "LUT": 15.24, "LUT_RAM": 16.94},
#     "V5.1": {"BRAM": 11.48, "DSP": 16.67, "FF": 3.42, "LUT": 15.31, "LUT_RAM": 16.94},
#     "V6.1": {"BRAM": 11.48, "DSP": 16.67, "FF": 16.49, "LUT": 58.92, "LUT_RAM": 0.77},
#     "V7.0": {"BRAM": 11.48, "DSP": 16.67, "FF": 17.3, "LUT": 65.4, "LUT_RAM": 0.77},
#     "V8.0\nx1": {"BRAM": 12.22, "DSP": 10.83, "FF": 3.41, "LUT": 8.9, "LUT_RAM": 0.77},
#     "V8.0\nx2": {"BRAM": 12.22, "DSP": 11.67, "FF": 3.41, "LUT": 8.96, "LUT_RAM": 0.77},
#     "V8.0\nx4": {"BRAM": 12.22, "DSP": 13.33, "FF": 3.41, "LUT": 9.11, "LUT_RAM": 0.77},
#     "V8.0\nx8": {"BRAM": 11.48, "DSP": 16.67, "FF": 3.41, "LUT": 10.99, "LUT_RAM": 4.94},
#     "V8.0\nx16": {"BRAM": 11.48, "DSP": 23.33, "FF": 3.42, "LUT": 13.2, "LUT_RAM": 9.11},
#     "V8.0\nx24": {"BRAM": 11.48, "DSP": 30.0, "FF": 3.42, "LUT": 15.39, "LUT_RAM": 13.27},
#     "V8.0\nx32": {"BRAM": 11.48, "DSP": 36.67, "FF": 3.43, "LUT": 17.56, "LUT_RAM": 17.44},
# }

# # Extract row and column labels
# row_labels = list(design_to_utilization.keys())
# column_labels = list(design_to_utilization[row_labels[0]].keys())

# # Extract values as a numpy array
# values = np.array(
#     [[design_to_utilization[row][col] for col in column_labels] for row in row_labels]
# )

# # Create a figure and axis
# fig, ax = plt.subplots()

# # Create the heatmap
# im = ax.imshow(values, cmap="YlOrRd")

# # Add colorbar
# cbar = ax.figure.colorbar(im, ax=ax)

# # Set the ticks and labels for x-axis and y-axis
# ax.set_xticks(np.arange(len(column_labels)))
# ax.set_yticks(np.arange(len(row_labels)))
# ax.set_xticklabels(column_labels)
# ax.set_yticklabels(row_labels)

# # Rotate the x-axis labels
# plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# # Loop over data dimensions and create text annotations
# for i in range(len(row_labels)):
#     for j in range(len(column_labels)):
#         text = ax.text(j, i, values[i, j], ha="center", va="center", color="black")

# # Set title and labels
# ax.set_title("Design Utilization Heatmap")
# ax.set_xlabel("Columns")
# ax.set_ylabel("Rows")

# # Display the plot
# plt.show()

import matplotlib.pyplot as plt
import numpy as np
import matplotlib

generate_pgf = True

if generate_pgf:
    matplotlib.use("pgf")
    matplotlib.rcParams.update({
        "pgf.texsystem": "pdflatex",
        'font.family': 'serif',
        'font.size': 7,
        'text.usetex': True,
        'pgf.rcfonts': False,
    })

# Data
design_to_utilization = {
    "NO_CFU": {"BRAM": 11.48, "DSP": 1.67, "FF": 2.89, "LUT": 7.15, "LUT_RAM": 0.77},
    "V4.0": {"BRAM": 11.48, "DSP": 9.58, "FF": 3.08, "LUT": 14.02, "LUT_RAM": 16.94},
    "V5.0": {"BRAM": 11.48, "DSP": 12.5, "FF": 3.24, "LUT": 15.24, "LUT_RAM": 16.94},
    "V5.1": {"BRAM": 11.48, "DSP": 16.67, "FF": 3.42, "LUT": 15.31, "LUT_RAM": 16.94},
    "V6.1": {"BRAM": 11.48, "DSP": 16.67, "FF": 16.49, "LUT": 58.92, "LUT_RAM": 0.77},
    "V7.0": {"BRAM": 11.48, "DSP": 16.67, "FF": 17.3, "LUT": 65.4, "LUT_RAM": 0.77},
    "V8.0\nx1": {"BRAM": 12.22, "DSP": 10.83, "FF": 3.41, "LUT": 8.9, "LUT_RAM": 0.77},
    "V8.0\nx2": {"BRAM": 12.22, "DSP": 11.67, "FF": 3.41, "LUT": 8.96, "LUT_RAM": 0.77},
    "V8.0\nx4": {"BRAM": 12.22, "DSP": 13.33, "FF": 3.41, "LUT": 9.11, "LUT_RAM": 0.77},
    "V8.0\nx8": {"BRAM": 11.48, "DSP": 16.67, "FF": 3.41, "LUT": 10.99, "LUT_RAM": 4.94},
    "V8.0\nx16": {"BRAM": 11.48, "DSP": 23.33, "FF": 3.42, "LUT": 13.2, "LUT_RAM": 9.11},
    "V8.0\nx24": {"BRAM": 11.48, "DSP": 30.0, "FF": 3.42, "LUT": 15.39, "LUT_RAM": 13.27},
    "V8.0\nx32": {"BRAM": 11.48, "DSP": 36.67, "FF": 3.43, "LUT": 17.56, "LUT_RAM": 17.44},
}

# Extract row and column labels
row_labels = list(design_to_utilization.keys())
column_labels = list(design_to_utilization[row_labels[0]].keys())

# Extract values as a numpy array and transpose
values = np.array([[design_to_utilization[row][col] for col in column_labels] for row in row_labels])
values = values.T  # Transpose the values

# Create a figure and axis
fig, ax = plt.subplots()

# Create the heatmap
# im = ax.imshow(values, cmap='YlOrRd')
im = ax.imshow(values, cmap='Blues')

# Add colorbar
cbar = ax.figure.colorbar(im, ax=ax)

# Set the ticks and labels for x-axis and y-axis
ax.set_xticks(np.arange(len(row_labels)))
ax.set_yticks(np.arange(len(column_labels)))
ax.set_xticklabels(row_labels)
ax.set_yticklabels(column_labels)

# Rotate the x-axis labels
plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

# Loop over data dimensions and create text annotations
for i in range(len(column_labels)):
    for j in range(len(row_labels)):
        color = "black"
        value = values[i, j]
        if value > 50:
            color = "white"
        text = ax.text(j, i, values[i, j], ha="center", va="center", color=color)

# Set title and labels
# ax.set_title("Design Utilization Heatmap (Transposed)")
ax.set_xlabel("CFU version")
ax.set_ylabel("Resource")

# Display the plot
if generate_pgf:
    # plt.savefig("cycle_bars_evolution.pgf")
    plt.savefig("resource_utilization.pgf")
else:
    plt.show()
