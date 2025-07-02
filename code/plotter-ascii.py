"""
iperf3 Network Performance Data Visualization Tool

This script processes iperf3 JSON output files and generates ASCII-based
graphical representations of network performance metrics including:
- Bidirectional throughput (sender/receiver bytes)
- Packet loss percentage
- Jitter measurements

The tool is designed for integration into IETF RFC documentation and
network performance analysis workflows.

Author: Ryan Rearden
License: MIT
Dependencies: gnuplot (external), python3 standard library

Shoutout to copilot for doing basically everything and making me question if I am really a programmer. 
"""

import configparser
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any


class ConfigManager:
    """
    Manages configuration settings from config.ini file.
    """
    
    def __init__(self, config_path: str = "config.ini"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = configparser.ConfigParser()
        self.config_path = Path(config_path)
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file, using defaults if file doesn't exist."""
        if self.config_path.exists():
            try:
                self.config.read(self.config_path)
                print(f"✓ Configuration loaded from {self.config_path}")
            except Exception as e:
                print(f"Warning: Error reading config file: {e}")
                self._set_defaults()
        else:
            print(f"Warning: Config file {self.config_path} not found, using defaults")
            self._set_defaults()
    
    def _set_defaults(self) -> None:
        """Set default configuration values."""
        self.config['DEFAULT'] = {
            'default_input_file': 'data/data.json',
            'default_output_dir': 'graphs_ascii',
            'graph_width': '120',
            'graph_height': '30',
            'precision_digits': '6',
            'plot_char_primary': '*',
            'plot_char_secondary': 'A',
            'plot_char_points': '+',
            'plot_style': 'linespoints',
            'show_ylabel_inline': 'true',
            'ylabel_position': 'left',
            'ylabel_rotation': 'vertical',
            'compact_ylabel': 'true',
            'show_axis_info_below': 'false',
            'terminal_type': 'dumb',
            'enable_grid': 'true',
            'enable_legend': 'true',
            'legend_position': 'top left',
            'skip_malformed_entries': 'true',
            'interpolate_missing_data': 'false',
            'include_timestamp': 'true',
            'include_metadata': 'true',
            'verbose_output': 'true',
            'track_sender_bytes': 'true',
            'track_receiver_bytes': 'true',
            'track_packet_loss': 'true',
            'track_jitter': 'true',
            'track_bandwidth': 'false',
            'track_retransmissions': 'false'
        }
    
    def get(self, key: str, fallback: str = '') -> str:
        """Get configuration value."""
        return self.config.get('DEFAULT', key, fallback=fallback)
    
    def get_bool(self, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value."""
        return self.config.getboolean('DEFAULT', key, fallback=fallback)
    
    def get_int(self, key: str, fallback: int = 0) -> int:
        """Get integer configuration value."""
        return self.config.getint('DEFAULT', key, fallback=fallback)


class IperfDataProcessor:
    """
    Process iperf3 JSON data and generate ASCII visualizations.
    """
    
    def __init__(self, json_file_path: str, output_directory: str = None, config: ConfigManager = None):
        """
        Initialize the processor with input and output paths.
        
        Args:
            json_file_path: Path to the iperf3 JSON data file
            output_directory: Directory for generated ASCII graphs (optional, uses config)
            config: Configuration manager instance
        """
        self.config = config or ConfigManager()
        self.json_file_path = Path(json_file_path)
        self.output_dir = Path(output_directory or self.config.get('default_output_dir'))
        self.json_name = self.json_file_path.stem
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Load and validate JSON data
        self.data = self._load_json_data()
    
    def _load_json_data(self) -> Dict[str, Any]:
        """
        Load and validate iperf3 JSON data.
        
        Returns:
            Parsed JSON data dictionary
            
        Raises:
            FileNotFoundError: If JSON file doesn't exist
            json.JSONDecodeError: If JSON is malformed
            ValueError: If required iperf3 data structure is missing
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Validate required iperf3 structure
            if 'intervals' not in data:
                raise ValueError("Invalid iperf3 JSON: missing 'intervals' section")
            
            return data
            
        except FileNotFoundError:
            print(f"Error: JSON file not found: {self.json_file_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    
    def extract_performance_metrics(self) -> Tuple[List[float], List[int], List[float], List[int], List[float], List[float]]:
        """
        Extract time-series performance metrics from iperf3 data.
        
        Returns:
            Tuple containing:
            - sender_times: Time points for sender data
            - sender_bytes: Bytes sent at each time point
            - receiver_times: Time points for receiver data  
            - receiver_bytes: Bytes received at each time point
            - packet_loss: Packet loss percentage at each time point
            - jitter: Jitter measurements in milliseconds
        """
        sender_times, sender_bytes = [], []
        receiver_times, receiver_bytes, packet_loss, jitter = [], [], [], []

        for interval in self.data.get("intervals", []):
            for stream in interval.get("streams", []):
                if stream.get("sender"):
                    sender_times.append(stream["end"])
                    sender_bytes.append(stream["bytes"])
                elif stream.get("sender") is False:
                    receiver_times.append(stream["end"])
                    receiver_bytes.append(stream["bytes"])
                    packet_loss.append(stream.get("lost_percent", 0))
                    jitter.append(stream.get("jitter_ms", 0))
                    
        return sender_times, sender_bytes, receiver_times, receiver_bytes, packet_loss, jitter

    def _write_data_file(self, filename: Path, x_data: List[float], y_data: List[float]) -> None:
        """
        Write time-series data to file in gnuplot format.
        
        Args:
            filename: Output file path
            x_data: X-axis data points (typically time)
            y_data: Y-axis data points (measurements)
        """
        precision = self.config.get_int('precision_digits', 6)
        format_str = f"{{:.{precision}f}}"
        
        with open(filename, "w", encoding='utf-8') as f:
            for x, y in zip(x_data, y_data):
                f.write(f"{format_str.format(x)} {format_str.format(y)}\n")

    def _generate_gnuplot_script(self, data_file: Path, title: str, 
                                x_label: str, y_label: str) -> str:
        """
        Generate gnuplot script for ASCII terminal output.
        
        Args:
            data_file: Path to data file
            title: Graph title
            x_label: X-axis label
            y_label: Y-axis label
            
        Returns:
            Gnuplot script content as string
        """
        # Get configuration values
        width = self.config.get_int('graph_width', 120)
        height = self.config.get_int('graph_height', 30)
        terminal = self.config.get('terminal_type', 'dumb')
        enable_grid = self.config.get_bool('enable_grid', True)
        enable_legend = self.config.get_bool('enable_legend', True)
        legend_pos = self.config.get('legend_position', 'top left')
        
        # Plot character customization
        primary_char = self.config.get('plot_char_primary', '*')
        secondary_char = self.config.get('plot_char_secondary', 'A')
        point_char = self.config.get('plot_char_points', '+')
        plot_style = self.config.get('plot_style', 'linespoints')
        
        # Y-axis configuration
        show_ylabel_inline = self.config.get_bool('show_ylabel_inline', True)
        compact_ylabel = self.config.get_bool('compact_ylabel', True)
        
        # Build gnuplot script with custom characters
        if terminal == 'dumb':
            script = f'set terminal {terminal} {width} {height} "{primary_char}{secondary_char}{point_char}"\n'
        else:
            script = f'set terminal {terminal} {width} {height}\n'
            
        script += f'set title "{title}"\n'
        # Don't set xlabel - we'll add it below the graph instead
        
        # Enhanced y-axis labeling
        if show_ylabel_inline and compact_ylabel:
            # Add a compact y-label that shows in the graph area
            script += f'set ylabel "{y_label}" offset 0,0\n'
            script += 'set format y "%.2g"\n'  # Use compact scientific notation
        else:
            script += f'set ylabel "{y_label}"\n'
        
        if enable_grid:
            script += 'set grid\n'
        
        if enable_legend:
            script += f'set key {legend_pos}\n'
        else:
            script += 'unset key\n'
        
        # Use custom plot style and ensure good character usage
        script += f'plot "{data_file}" using 1:2 with {plot_style} title ""\n'
        
        return script

    def _execute_gnuplot(self, script_content: str, script_file: Path, 
                        output_file: Path, y_label: str = "", x_label: str = "") -> bool:
        """
        Execute gnuplot script and save ASCII output.
        
        Args:
            script_content: Gnuplot script content
            script_file: Path to save script file
            output_file: Path to save ASCII graph output
            y_label: Y-axis label for post-processing
            x_label: X-axis label for post-processing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Write gnuplot script
            with open(script_file, "w", encoding='utf-8') as f:
                f.write(script_content)
            
            # Execute gnuplot
            result = subprocess.run(
                ["gnuplot", script_file], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Save ASCII output with post-processing
            raw_output = result.stdout
            processed_output = self._post_process_ascii_output(raw_output, y_label, x_label)
            
            with open(output_file, "w", encoding='utf-8') as out:
                out.write(processed_output)
                
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error executing gnuplot: {e}")
            return False
        except FileNotFoundError:
            print("Error: gnuplot not found. Please install gnuplot.")
            return False

    def _post_process_ascii_output(self, raw_output: str, y_label: str, x_label: str = "") -> str:
        """
        Post-process ASCII output to add better y-axis labeling and custom characters.
        
        Args:
            raw_output: Raw ASCII output from gnuplot
            y_label: Y-axis label to add
            x_label: X-axis label for below-graph info
            
        Returns:
            Enhanced ASCII output with better y-axis labeling and custom characters
        """
        lines = raw_output.split('\n')
        if not lines:
            return raw_output
        
        # Replace default plot characters with custom ones
        primary_char = self.config.get('plot_char_primary', '*')
        secondary_char = self.config.get('plot_char_secondary', 'A')
        point_char = self.config.get('plot_char_points', '+')
        
        # Find the graph area first (lines with plot data)
        graph_start = -1
        graph_end = -1
        
        for i, line in enumerate(lines):
            # Look for lines that contain the vertical borders |
            if '|' in line and len(line) > 50:
                if graph_start == -1:
                    graph_start = i
                graph_end = i
        
        # Replace characters in all lines (except specific text we want to preserve)
        for i, line in enumerate(lines):
            # Skip title line and specific text labels
            if any(phrase in line for phrase in ['Network', 'Measurement Data', 'X Axis:', 'Y Axis:']):
                continue
                
            # Replace * with custom primary character
            if '*' in line and primary_char != '*':
                line = line.replace('*', primary_char)
                
            # Replace ALL A characters with custom secondary character (except in specific protected text)
            if 'A' in line and secondary_char != 'A':
                line = line.replace('A', secondary_char)
                
            # Remove all dashes and underscores
            line = line.replace('-', ' ').replace('_', ' ')

            # Remove plot points and '+' characters 
            if '+' in line:
                line = line.replace('+', ' ')
                
            lines[i] = line
            
        # Add top and bottom borders to enclose the graph in a box
        if graph_start != -1 and graph_end != -1:
            # Find a typical line with | characters to get the exact positions
            typical_pipe_start = -1
            typical_pipe_end = -1
            
            for i in range(graph_start, graph_end + 1):
                if '|' in lines[i]:
                    line = lines[i]
                    first_pipe = line.find('|')
                    last_pipe = line.rfind('|')
                    if typical_pipe_start == -1:
                        typical_pipe_start = first_pipe
                        typical_pipe_end = last_pipe
                    break
            
            # Calculate border length based on the actual | positions
            if typical_pipe_start != -1 and typical_pipe_end != -1:
                border_length = typical_pipe_end - typical_pipe_start - 1
            else:
                # Fallback if no | characters found
                border_length = 60
            
            # Find the first and last lines with y-axis values that start at the beginning of the line
            first_y_line = -1
            last_y_line = -1
            
            for i in range(len(lines)):
                # Look for lines that start with y-axis values (numbers at start of line)
                line_stripped = lines[i].strip()
                if line_stripped:
                    # Check if line starts with a number (scientific notation or regular number)
                    # Look for patterns like "1.5e 07", "1e 07", "9e 06", etc.
                    # But exclude X-axis scale lines that start with just "0"
                    if (line_stripped[0].isdigit() or 
                        (len(line_stripped) > 1 and line_stripped[0] == '0' and line_stripped[1] == '.') or
                        line_stripped.startswith(tuple('123456789'))):
                        # Additional check to make sure this looks like a y-axis value
                        # and NOT an x-axis scale (which would have multiple numbers separated by spaces)
                        if ('e ' in line_stripped or 'e+' in line_stripped or 'e-' in line_stripped):
                            # This is scientific notation, likely a y-axis value
                            if first_y_line == -1:
                                first_y_line = i
                            last_y_line = i
                        elif line_stripped.count(' ') <= 2 and any(c.isdigit() for c in line_stripped[:15]):
                            # This might be a regular number y-axis value (not x-axis scale)
                            # X-axis scales typically have many space-separated numbers
                            if not re.match(r'^\s*\d+\s+\d+\s+\d+', line_stripped):  # Not an x-axis scale
                                if first_y_line == -1:
                                    first_y_line = i
                                last_y_line = i
            
            # Insert borders aligned with the first and last y-axis labels
            if first_y_line != -1 and last_y_line != -1 and typical_pipe_start != -1:
                # Replace the first y-axis label line with a border
                if first_y_line < len(lines):
                    line = lines[first_y_line]
                    # Extract the y-axis value - improved regex to capture full scientific notation
                    match = re.search(r'^\s*([0-9.e+\-\s]+)', line)
                    if match:
                        y_value = match.group(1).strip()
                        # Right-align the y-axis value to match other lines
                        # The pipe position minus 1 space should be where the y-axis value ends
                        y_value_end_pos = typical_pipe_start - 1
                        padding_needed = y_value_end_pos - len(y_value)
                        if padding_needed > 0:
                            border_line = ' ' * padding_needed + y_value + ' ' + '+' + '-' * border_length + '+'
                        else:
                            # If y_value is too long, just use minimal formatting
                            border_line = y_value + ' ' + '+' + '-' * border_length + '+'
                        lines[first_y_line] = border_line
                
                # Replace the last y-axis label line with a border
                if last_y_line < len(lines):
                    line = lines[last_y_line]
                    # Extract the y-axis value - improved regex to capture full scientific notation
                    match = re.search(r'^\s*([0-9.e+\-\s]+)', line)
                    if match:
                        y_value = match.group(1).strip()
                        # Right-align the y-axis value to match other lines
                        # The pipe position minus 1 space should be where the y-axis value ends
                        y_value_end_pos = typical_pipe_start - 1
                        padding_needed = y_value_end_pos - len(y_value)
                        if padding_needed > 0:
                            border_line = ' ' * padding_needed + y_value + ' ' + '+' + '-' * border_length + '+'
                        else:
                            # If y_value is too long, just use minimal formatting
                            border_line = y_value + ' ' + '+' + '-' * border_length + '+'
                        lines[last_y_line] = border_line
        
        # Add vertical y-axis label if configured
        if self.config.get_bool('show_ylabel_inline', True):
            ylabel_rotation = self.config.get('ylabel_rotation', 'vertical')
            ylabel_position = self.config.get('ylabel_position', 'left')
            
            if ylabel_rotation == 'vertical' and ylabel_position == 'left':
                # Add vertical y-label on the left side
                y_chars = list(y_label.replace(' ', '_'))
                
                # Find the middle of the graph for vertical centering
                graph_height = graph_end - graph_start
                middle_start = graph_start + graph_height // 2 - len(y_chars) // 2
                
                for i, char in enumerate(y_chars):
                    line_idx = middle_start + i
                    if 0 <= line_idx < len(lines):
                        # Add the character at the beginning of the line
                        lines[line_idx] = char + ' ' + lines[line_idx]
                        
                # Add spacing to other lines to maintain alignment
                for i in range(len(lines)):
                    if graph_start <= i <= graph_end and i not in range(middle_start, middle_start + len(y_chars)):
                        lines[i] = '  ' + lines[i]
        
        # Add axis information below the graph if configured
        if self.config.get_bool('show_axis_info_below', False):
            # Remove the last 2 empty lines if they exist to move labels up 2 spaces
            while lines and lines[-1].strip() == '':
                lines.pop()
            
            # Add axis information with minimal spacing
            lines.append('')
            lines.append(f'X Axis: {x_label}')
            lines.append(f'Y Axis: {y_label}')
        
        return '\n'.join(lines)

    def generate_ascii_graphs(self) -> None:
        """
        Generate ASCII graphs for all performance metrics.
        
        Creates visualizations based on configuration settings.
        """
        verbose = self.config.get_bool('verbose_output', True)
        
        if verbose:
            print("Extracting performance metrics from iperf3 data...")
        
        sender_times, sender_bytes, receiver_times, receiver_bytes, packet_loss, jitter = self.extract_performance_metrics()
        
        # Define datasets with metadata - filter based on config
        all_datasets = [
            ("senderBytes", sender_times, sender_bytes, 
             "Network Throughput: Sender Bytes Over Time", "Time (seconds)", "Bytes Transmitted",
             self.config.get_bool('track_sender_bytes', True)),
            ("receiverBytes", receiver_times, receiver_bytes, 
             "Network Throughput: Receiver Bytes Over Time", "Time (seconds)", "Bytes Received",
             self.config.get_bool('track_receiver_bytes', True)),
            ("packetLoss", receiver_times, packet_loss, 
             "Network Quality: Packet Loss Percentage Over Time", "Time (seconds)", "Packet Loss (%)",
             self.config.get_bool('track_packet_loss', True)),
            ("jitter", receiver_times, jitter, 
             "Network Quality: Jitter Measurements Over Time", "Time (seconds)", "Jitter (ms)",
             self.config.get_bool('track_jitter', True))
        ]
        
        # Filter datasets based on configuration
        datasets = [(name, x, y, title, xlabel, ylabel) for name, x, y, title, xlabel, ylabel, enabled in all_datasets if enabled]

        successful_graphs = 0
        
        for metric_name, x_data, y_data, title, x_label, y_label in datasets:
            if not x_data or not y_data:
                if verbose:
                    print(f"Warning: No data available for {metric_name}")
                continue
                
            # Generate file paths
            data_file = self.output_dir / f"{metric_name}_{self.json_name}.dat"
            script_file = self.output_dir / f"{metric_name}_{self.json_name}.plt" 
            output_file = self.output_dir / f"{metric_name}_{self.json_name}.txt"

            if verbose:
                print(f"Generating {metric_name} visualization...")
            
            # Write data file
            self._write_data_file(data_file, x_data, y_data)
            
            # Generate and execute gnuplot script
            script = self._generate_gnuplot_script(data_file, title, x_label, y_label)
            
            if self._execute_gnuplot(script, script_file, output_file, y_label, x_label):
                successful_graphs += 1
                if verbose:
                    print(f"  ✓ {metric_name} graph saved to {output_file}")
            else:
                if verbose:
                    print(f"  ✗ Failed to generate {metric_name} graph")

        if verbose:
            print(f"\nProcessing complete: {successful_graphs}/{len(datasets)} graphs generated successfully")
            print(f"ASCII graphs saved in: {self.output_dir}")


def main():
    """
    Main entry point for the iperf3 visualization tool.
    """
    # Load configuration
    config = ConfigManager()
    
    # Get configuration values
    default_json_path = config.get('default_input_file', 'data/data.json')
    default_output_dir = config.get('default_output_dir', 'graphs_ascii')
    verbose = config.get_bool('verbose_output', True)
    
    # Allow command line override of input file
    json_path = sys.argv[1] if len(sys.argv) > 1 else default_json_path
    
    if verbose:
        print("iperf3 Network Performance Visualization Tool")
        print("=" * 50)
        print(f"Input file: {json_path}")
        print(f"Output directory: {default_output_dir}")
        print(f"Graph dimensions: {config.get_int('graph_width')}x{config.get_int('graph_height')}")
        print(f"Grid enabled: {config.get_bool('enable_grid')}")
        print(f"Legend enabled: {config.get_bool('enable_legend')}")
        print()
    
    try:
        # Initialize processor and generate graphs
        processor = IperfDataProcessor(json_path, default_output_dir, config)
        processor.generate_ascii_graphs()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
