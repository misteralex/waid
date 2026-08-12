{% macro dump_vars() %}
  {# Define the list of variable keys you want to inspect #}
  {% set target_keys = [
    'max_bias_temp', 
    'max_bias_pres', 
    'max_bias_rh', 
    'max_bias_wind', 
    'max_bias_solar', 
    'max_bias_rain'
  ] %}
  
  {# Build a standard dictionary by fetching each variable safely #}
  {% set resolved_vars = {} %}
  {% for key in target_keys %}
    {% do resolved_vars.update({key: var(key, none)}) %}
  {% endfor %}
  
  {# Log the clean JSON representation #}
  {{ log(tojson(resolved_vars), info=True) }}
{% endmacro %}